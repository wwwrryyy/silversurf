import { RateUnit } from '../types';

/**
 * Standard Indian GST rate for Silver Bullion is 3%.
 */
export const GST_RATE = 0.03;

/**
 * Calculates rate including 3% GST (derived benchmark).
 */
export function calculateWithGST(basePrice: number): number {
  return Number((basePrice * (1 + GST_RATE)).toFixed(2));
}

/**
 * Converts a base price (assumed per 1 kg) into the requested display unit:
 * - 'per_kg': basePrice
 * - 'per_10g': basePrice / 100
 * - 'per_gram': basePrice / 1000
 */
export function convertRateUnit(pricePerKg: number, unit: RateUnit): number {
  switch (unit) {
    case 'per_10g':
      return Number((pricePerKg / 100).toFixed(2));
    case 'per_gram':
      return Number((pricePerKg / 1000).toFixed(3));
    case 'per_kg':
    default:
      return Number(pricePerKg.toFixed(2));
  }
}

/**
 * Returns unit label for UI presentation.
 */
export function getUnitDisplayLabel(unit: RateUnit): string {
  switch (unit) {
    case 'per_10g':
      return '/ 10g';
    case 'per_gram':
      return '/ g';
    case 'per_kg':
    default:
      return '/ kg';
  }
}
