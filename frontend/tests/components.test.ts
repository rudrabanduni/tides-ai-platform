import { describe, it, expect } from 'vitest';
import { mapRecommendation } from '../components/SupervisoryReviewView';
import { getVerificationMeta } from '../components/VerificationBadge';

describe('Supervisory Review Recommendation Mapping', () => {
  it('maps INCUBATE to Support', () => {
    const res = mapRecommendation('INCUBATE');
    expect(res.display).toBe('Support');
    expect(res.badgeClass).toContain('emerald');
  });

  it('maps SUPPORT and APPROVE to Support', () => {
    expect(mapRecommendation('SUPPORT').display).toBe('Support');
    expect(mapRecommendation('APPROVE').display).toBe('Support');
  });

  it('maps CONDITIONAL and DEFER to Nurture', () => {
    const resCond = mapRecommendation('CONDITIONAL');
    expect(resCond.display).toBe('Nurture');
    expect(resCond.badgeClass).toContain('amber');

    const resDefer = mapRecommendation('DEFER');
    expect(resDefer.display).toBe('Nurture');
    expect(resDefer.badgeClass).toContain('amber');
  });

  it('maps REJECT and DECLINE to Decline', () => {
    const res = mapRecommendation('REJECT');
    expect(res.display).toBe('Decline');
    expect(res.badgeClass).toContain('rose');

    const resDec = mapRecommendation('DECLINE');
    expect(resDec.display).toBe('Decline');
    expect(resDec.badgeClass).toContain('rose');
  });

  it('handles unknown or empty recommendations by defaulting to Nurture', () => {
    expect(mapRecommendation('').display).toBe('Nurture');
    expect(mapRecommendation(undefined).display).toBe('Nurture');
  });
});

describe('VerificationBadge Meta Mapping', () => {
  it('correctly maps VERIFIED_DOCUMENTED', () => {
    const meta = getVerificationMeta('VERIFIED_DOCUMENTED');
    expect(meta.label).toBe('Verified (Documented)');
    expect(meta.shortLabel).toBe('Verified');
    expect(meta.bgClass).toContain('emerald');
  });

  it('correctly maps SELF_REPORTED_ONLY', () => {
    const meta = getVerificationMeta('SELF_REPORTED_ONLY');
    expect(meta.label).toBe('Self-Reported Only');
    expect(meta.bgClass).toContain('amber');
  });

  it('correctly maps PLAUSIBLE_ESTIMATE', () => {
    const meta = getVerificationMeta('PLAUSIBLE_ESTIMATE');
    expect(meta.label).toBe('Plausible Estimate');
    expect(meta.bgClass).toContain('blue');
  });

  it('correctly maps UNSUPPORTED_ASSUMPTION', () => {
    const meta = getVerificationMeta('UNSUPPORTED_ASSUMPTION');
    expect(meta.label).toBe('Unsupported Assumption');
    expect(meta.bgClass).toContain('orange');
  });

  it('correctly maps CONTRADICTED', () => {
    const meta = getVerificationMeta('CONTRADICTED');
    expect(meta.label).toBe('Contradicted');
    expect(meta.bgClass).toContain('rose');
  });

  it('correctly maps MISSING_INFORMATION without zeroing out', () => {
    const meta = getVerificationMeta('MISSING_INFORMATION');
    expect(meta.label).toBe('Missing Information');
    expect(meta.shortLabel).toBe('Missing');
    expect(meta.bgClass).toContain('slate');
  });

  it('correctly maps NOT_APPLICABLE', () => {
    const meta = getVerificationMeta('NOT_APPLICABLE');
    expect(meta.label).toBe('Not Applicable');
    expect(meta.shortLabel).toBe('N/A');
  });

  it('handles undefined or null status honestly as Not Assessed', () => {
    const metaNull = getVerificationMeta(null);
    expect(metaNull.label).toBe('Not Assessed');

    const metaUndef = getVerificationMeta(undefined);
    expect(metaUndef.label).toBe('Not Assessed');
  });
});
