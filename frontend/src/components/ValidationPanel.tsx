import type { ValidationResult } from '../types';

export function ValidationPanel({ result }: { result: ValidationResult | null }) {
  if (!result) {
    return <div className="muted">尚未校验。</div>;
  }
  return (
    <div className={result.passed ? 'validation passed' : 'validation failed'}>
      <strong>{result.passed ? '校验通过' : '校验未通过'}</strong>
      {[...result.errors, ...result.warnings].map((item, index) => (
        <p key={index}>{item.message}</p>
      ))}
    </div>
  );
}
