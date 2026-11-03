import React from 'react';
import { ExternalLink, ShieldAlert } from 'lucide-react';

export const Attribution: React.FC = () => {
  return (
    <footer className="mt-16 border-t border-white/10 bg-claude-surface-dark text-claude-on-dark-soft py-10 px-4 sm:px-8 text-xs font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Attribution & Legal Notice */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 pb-5 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            {/* Claude-style coral mark */}
            <svg
              className="h-4 w-4 text-claude-primary shrink-0"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M12 2l1.5 6.5L20 10l-5.5 3.5L16 20l-4-4.5L8 20l1.5-6.5L4 10l6.5-1.5L12 2z" />
            </svg>
            <span className="text-claude-on-dark font-medium">
              Source Attribution:{' '}
              <a
                href="https://ibjarates.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-claude-primary hover:underline underline-offset-2 inline-flex items-center gap-1"
              >
                India Bullion and Jewellers Association (ibjarates.com)
                <ExternalLink className="h-3 w-3 inline" aria-hidden="true" />
              </a>
            </span>
          </div>

          <div className="text-[11px] text-claude-on-dark-soft">
            Zaveri Bazar, Mumbai, India • Official Benchmark Publisher
          </div>
        </div>

        {/* Disclaimer per PRD §11.4 */}
        <div className="flex items-start gap-2.5 text-[11px] text-claude-on-dark-soft leading-relaxed bg-claude-surface-dark-elevated p-4 rounded-claude-md border border-white/5">
          <ShieldAlert className="h-4 w-4 text-claude-amber shrink-0 mt-0.5" aria-hidden="true" />
          <p>
            <strong className="text-claude-on-dark">Benchmark Notice & Disclaimer:</strong> Silver 999 rates
            published on this dashboard reflect opening (AM) and closing (PM) benchmarks collected from physical
            market participants in Mumbai. Rates exclude 3% Goods and Services Tax (GST) and jeweller making charges
            unless viewed with the derived GST toggle. SilverSurf is designed strictly for personal, non-commercial
            monitoring and does not constitute trading, valuation, or investment advice. For commercial valuation,
            retail pricing, lending apps, or automated transactions, subscribe directly to the official IBJA API.
          </p>
        </div>

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-2 text-[10px] text-claude-on-dark-soft">
          <span>SilverSurf • Warm Editorial Terminal</span>
          <span>Timezone: Asia/Kolkata (IST) • Detection timestamps in UTC ISO-8601</span>
        </div>
      </div>
    </footer>
  );
};
