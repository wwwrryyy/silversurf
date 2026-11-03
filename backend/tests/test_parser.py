from datetime import date
from pathlib import Path
import pytest

from app.core.errors import ParserIntegrityError
from app.domain.metal import Metal, Session
from app.sources.ibja_html import IbjaHtmlSource

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_ibja_html_source_parses_sample_page():
    html_bytes = (FIXTURES_DIR / "sample_page.html").read_bytes()
    source = IbjaHtmlSource()

    results = source.parse_html(html_bytes, http_status=200, source_url="https://ibjarates.com/")
    assert len(results) == 5

    # Check AM rows
    am_rows = [r for r in results if r.session == Session.AM]
    assert len(am_rows) == 3

    r1 = am_rows[0]
    assert r1.rate_date == date(2026, 11, 2)
    assert r1.metal == Metal.SILVER
    assert r1.purity == "999"
    assert r1.price_inr == 98500.0
    assert r1.card_price_inr == 98500.0

    r2 = am_rows[1]
    assert r2.rate_date == date(2026, 10, 31)
    assert r2.price_inr == 97950.0

    # Check PM rows
    pm_rows = [r for r in results if r.session == Session.PM]
    assert len(pm_rows) == 2
    assert pm_rows[0].rate_date == date(2026, 10, 31)
    assert pm_rows[0].price_inr == 98100.0


def test_ibja_html_source_shifted_columns():
    """Verify parser finds 'Silver 999' by text header, never by fixed index."""
    shifted_html = """
    <html><body>
        <h2>Opening Rates (AM)</h2>
        <table id="tblOpening">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Silver 999</th>
                    <th>Gold 999</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>02/11/2026</td>
                    <td>98,500</td>
                    <td>78,500</td>
                </tr>
            </tbody>
        </table>
    </body></html>
    """.encode("utf-8")

    source = IbjaHtmlSource()
    results = source.parse_html(shifted_html, http_status=200)
    assert len(results) == 1
    assert results[0].price_inr == 98500.0
    assert results[0].rate_date == date(2026, 11, 2)
    assert results[0].session == Session.AM


def test_ibja_html_source_malformed_raises_error():
    malformed_bytes = (FIXTURES_DIR / "sample_page_malformed.html").read_bytes()
    source = IbjaHtmlSource()
    with pytest.raises(ParserIntegrityError):
        source.parse_html(malformed_bytes, http_status=200)


def test_ibja_html_source_unified_am_pm_columns():
    """Verify parser extracts both AM and PM when listed in separate columns in a single table."""
    unified_html = """
    <html><body>
        <table id="tblUnifiedRates">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Gold 999 (AM)</th>
                    <th>Gold 999 (PM)</th>
                    <th>Silver 999 (AM Price)</th>
                    <th>Silver 999 (PM Price)</th>
                    <th>Platinum 999</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>30/10/2026</td>
                    <td>140891</td>
                    <td>140054</td>
                    <td>183,800</td>
                    <td>181,344</td>
                    <td>59303</td>
                </tr>
                <tr>
                    <td>29/10/2026</td>
                    <td>142144</td>
                    <td>142255</td>
                    <td>190,497</td>
                    <td>190,478</td>
                    <td>61620</td>
                </tr>
            </tbody>
        </table>
    </body></html>
    """.encode("utf-8")

    source = IbjaHtmlSource()
    results = source.parse_html(unified_html, http_status=200)
    assert len(results) == 4

    am_results = [r for r in results if r.session == Session.AM]
    pm_results = [r for r in results if r.session == Session.PM]

    assert len(am_results) == 2
    assert len(pm_results) == 2

    # Check 30/10 rates
    r_30_am = next(r for r in am_results if r.rate_date == date(2026, 10, 30))
    r_30_pm = next(r for r in pm_results if r.rate_date == date(2026, 10, 30))
    assert r_30_am.price_inr == 183800.0
    assert r_30_pm.price_inr == 181344.0

    # Check 29/10 rates
    r_29_am = next(r for r in am_results if r.rate_date == date(2026, 10, 29))
    r_29_pm = next(r for r in pm_results if r.rate_date == date(2026, 10, 29))
    assert r_29_am.price_inr == 190497.0
    assert r_29_pm.price_inr == 190478.0

    # Ensure Platinum rate (59303, 61620) was NEVER extracted as silver
    assert all(r.price_inr not in (59303.0, 61620.0) for r in results)
