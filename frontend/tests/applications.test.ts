import { describe, expect, it } from 'vitest';
import { apiErrorMessage, MAX_UPLOAD_BYTES, validateUploadFile } from '@/services/applications';

function fakeFile(name: string, size: number): File {
  return { name, size } as unknown as File;
}

describe('validateUploadFile', () => {
  it('accepts supported document types within the size limit', () => {
    for (const name of ['deck.pdf', 'cv.DOCX', 'model.xlsx', 'notes.md', 'slides.pptx']) {
      expect(validateUploadFile(fakeFile(name, 1024))).toBeNull();
    }
  });

  it('rejects executables and files without an extension', () => {
    expect(validateUploadFile(fakeFile('malware.exe', 10))).toMatch(/Unsupported file type/);
    expect(validateUploadFile(fakeFile('noextension', 10))).toMatch(/Unsupported file type/);
  });

  it('rejects empty and oversized files', () => {
    expect(validateUploadFile(fakeFile('deck.pdf', 0))).toMatch(/empty/);
    expect(validateUploadFile(fakeFile('deck.pdf', MAX_UPLOAD_BYTES + 1))).toMatch(/25 MB/);
  });
});

describe('apiErrorMessage', () => {
  it('prefers backend detail strings', () => {
    expect(apiErrorMessage({ response: { data: { detail: 'Rejected file' } } })).toBe('Rejected file');
  });
  it('joins pydantic validation errors', () => {
    expect(apiErrorMessage({ response: { data: { detail: [{ msg: 'a' }, { msg: 'b' }] } } })).toBe('a; b');
  });
  it('falls back to the provided message', () => {
    expect(apiErrorMessage({}, 'fallback')).toBe('fallback');
  });
});
