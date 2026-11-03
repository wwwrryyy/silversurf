/**
 * Formatting utilities for Indian Rupee currency, dates, and timestamps in Asia/Kolkata (IST).
 */

/**
 * Format a number as Indian Rupee (INR) currency with Indian commas (Lakhs/Crores).
 * Example: 98500 -> "₹98,500.00"
 */
export function formatINR(amount: number | null | undefined, decimals: number = 2): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '₹--';
  }

  const parts = amount.toFixed(decimals).split('.');
  const integerPart = parts[0];
  const decimalPart = parts[1];

  // Apply Indian grouping: last 3 digits, then groups of 2 digits
  let lastThree = integerPart.slice(-3);
  const otherNumbers = integerPart.slice(0, -3);

  if (otherNumbers !== '') {
    lastThree = ',' + lastThree;
  }

  const formattedInteger =
    otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + lastThree;

  return decimals > 0 ? `₹${formattedInteger}.${decimalPart}` : `₹${formattedInteger}`;
}

/**
 * Format a date string (YYYY-MM-DD) into display format (e.g. "02 Nov 2026").
 */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '--';
  try {
    const [year, month, day] = dateStr.split('-');
    if (!year || !month || !day) return dateStr;
    const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    return date.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

/**
 * Format ISO timestamp into IST (Asia/Kolkata) time.
 * Example: "12:06:12 PM IST"
 */
export function formatISTTime(isoTimestamp: string | null | undefined): string {
  if (!isoTimestamp) return '--:--:-- IST';
  try {
    const date = new Date(isoTimestamp);
    if (isNaN(date.getTime())) return '--:--:-- IST';
    return (
      new Intl.DateTimeFormat('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      }).format(date) + ' IST'
    );
  } catch {
    return '--:--:-- IST';
  }
}

/**
 * Format ISO timestamp into full IST date and time.
 * Example: "02 Nov 2026, 12:06:12 PM IST"
 */
export function formatISTDateTime(isoTimestamp: string | null | undefined): string {
  if (!isoTimestamp) return '--';
  try {
    const date = new Date(isoTimestamp);
    if (isNaN(date.getTime())) return '--';
    const formatted = new Intl.DateTimeFormat('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    }).format(date);
    return `${formatted} IST`;
  } catch {
    return '--';
  }
}

/**
 * Format percentage move with sign and precision.
 * Example: +1.24% or -0.85%
 */
export function formatPercentage(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return '0.00%';
  const prefix = val > 0 ? '+' : '';
  return `${prefix}${val.toFixed(2)}%`;
}

/**
 * Format a date as YYYY-MM-DD in Asia/Kolkata (IST).
 */
export function formatISTDateISO(date: Date): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date);
}

/**
 * Compute inclusive from/to date strings (IST) for a history range filter.
 * Returns null for the 'ALL' range.
 */
export function getISTDateRange(
  rangeFilter: '7D' | '30D' | '90D' | 'ALL'
): { fromDate: string; toDate: string } | null {
  if (rangeFilter === 'ALL') return null;
  const daysMap = { '7D': 7, '30D': 30, '90D': 90 } as const;
  const now = new Date();
  const from = new Date(now.getTime() - daysMap[rangeFilter] * 24 * 60 * 60 * 1000);
  return { fromDate: formatISTDateISO(from), toDate: formatISTDateISO(now) };
}
