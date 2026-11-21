import { describe, it, expect } from 'vitest';
import { CANONICAL_DOMAINS, resolveDomainData } from '../components/CanonicalDomainsView';
import { DomainAssessmentReport } from '../types';

describe('Canonical Domain Registry & Mappings Audit', () => {
  it('contains exactly six unique canonical evaluation domains', () => {
    expect(CANONICAL_DOMAINS.length).toBe(6);
    const keys = CANONICAL_DOMAINS.map(d => d.key);
    expect(new Set(keys).size).toBe(6);

    expect(keys).toEqual([
      'problem_solution',
      'market_opportunity',
      'founder_team',
      'commercialisation',
      'innovation_impact',
      'financials_support',
    ]);
  });

  it('correctly maps canonical titles and criteria prefixes', () => {
    const ps = CANONICAL_DOMAINS.find(d => d.key === 'problem_solution')!;
    expect(ps.title).toBe('Problem & Solution');
    expect(ps.criteriaPrefix).toContain('PS-01 to PS-13');
    expect(ps.slides).toBe('Slides 3–5');

    const mo = CANONICAL_DOMAINS.find(d => d.key === 'market_opportunity')!;
    expect(mo.title).toBe('Market Opportunity & Competition');
    expect(mo.criteriaPrefix).toContain('MO-01 to MO-10');

    const ft = CANONICAL_DOMAINS.find(d => d.key === 'founder_team')!;
    expect(ft.title).toBe('Founder & Team Capability');
    expect(ft.criteriaPrefix).toContain('FT-01 to FT-13');

    const bc = CANONICAL_DOMAINS.find(d => d.key === 'commercialisation')!;
    expect(bc.title).toBe('Business Model & Commercialisation');
    expect(bc.criteriaPrefix).toContain('BC-01 to BC-16');

    const ii = CANONICAL_DOMAINS.find(d => d.key === 'innovation_impact')!;
    expect(ii.title).toBe('Innovation, IP & Impact');
    expect(ii.criteriaPrefix).toContain('II-01 to II-14');

    const fi = CANONICAL_DOMAINS.find(d => d.key === 'financials_support')!;
    expect(fi.title).toBe('Financials & Incubation Support');
    expect(fi.criteriaPrefix).toContain('FI-01 to FI-21');
  });

  it('traces Technology & TRL findings to Domain 1 (Problem & Solution)', () => {
    const mockPSReport: DomainAssessmentReport = {
      domain: 'problem_solution',
      domain_key: 'problem_solution',
      domain_title: 'Problem & Solution',
      summary: 'Strong technical validation and TRL 5 prototype.',
      composite_domain_confidence: 0.90,
      criteria_evaluations: {
        'PS-09': {
          criterion_id: 'PS-09',
          criterion_name: 'Current TRL & Justification',
          extracted_startup_response: 'TRL 5 tested in vacuum',
          assessment_narrative: 'NASA standard TRL-5 verification confirmed.',
          verification_status: 'VERIFIED_DOCUMENTED',
          source_locations: ['Slide 5'],
          confidence_score: 0.92,
        },
      },
    };

    const domainReports = { problem_solution: mockPSReport };

    // Query for 'trl' alias
    const trlResolution = resolveDomainData('trl', domainReports);
    expect(trlResolution.report).toBe(mockPSReport);
    expect(trlResolution.sourceKey).toBe('problem_solution');
    expect(trlResolution.provenanceNote).toContain('LaunchIndex Domain 1 (Problem & Solution)');
    expect(trlResolution.provenanceNote).toContain('Criteria PS-09 to PS-13');

    // Query for 'technology' alias
    const techResolution = resolveDomainData('technology', domainReports);
    expect(techResolution.report).toBe(mockPSReport);
    expect(techResolution.sourceKey).toBe('problem_solution');
  });

  it('supports legacy graph assessment aliases without crashing', () => {
    const legacyGraph = {
      domain_assessments: {
        product: { summary: 'Legacy product analysis', composite_domain_confidence: 0.8 },
        market: { summary: 'Legacy market analysis', composite_domain_confidence: 0.75 },
        founder: { summary: 'Legacy founder analysis', composite_domain_confidence: 0.85 },
        commercialization: { summary: 'Legacy commercialization analysis', composite_domain_confidence: 0.7 },
        ip: { summary: 'Legacy IP analysis', composite_domain_confidence: 0.8 },
        financial: { summary: 'Legacy financial analysis', composite_domain_confidence: 0.65 },
      },
    };

    expect(resolveDomainData('problem_solution', {}, legacyGraph).report?.summary).toBe('Legacy product analysis');
    expect(resolveDomainData('market_opportunity', {}, legacyGraph).report?.summary).toBe('Legacy market analysis');
    expect(resolveDomainData('founder_team', {}, legacyGraph).report?.summary).toBe('Legacy founder analysis');
    expect(resolveDomainData('commercialisation', {}, legacyGraph).report?.summary).toBe('Legacy commercialization analysis');
    expect(resolveDomainData('innovation_impact', {}, legacyGraph).report?.summary).toBe('Legacy IP analysis');
    expect(resolveDomainData('financials_support', {}, legacyGraph).report?.summary).toBe('Legacy financial analysis');
  });

  it('handles missing domains gracefully without returning undefined scores', () => {
    const res = resolveDomainData('non_existent_domain', {});
    expect(res.report).toBeNull();
    expect(res.sourceKey).toBe('non_existent_domain');
  });
});
