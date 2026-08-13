"""
Vahan Public Report - form filler
==================================

Y-Axis:
    vehicleMakerName

X-Axis:
    monthWise / Month Wise

CAPTCHA:
    Manual entry only. No OCR or automatic solving.

FIX APPLIED (see comments marked "FIX"):
    Selecting Y-Axis fires the site's onchange handler, which kicks off an
    AJAX call that rebuilds/resets #xAxis. If X-Axis is touched before that
    call finishes, the selection gets silently overwritten a moment later -
    which is exactly the "X-Axis won't select" symptom you were hitting.
    The fix waits for the network to go idle (and adds a small buffer)
    after the Y-Axis change, before touching X-Axis at all.
"""

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError


URL = "https://analytics.parivahan.gov.in/analytics/vahanpublicreport"

Y_AXIS_VALUE = "vehicleMakerName"
X_AXIS_VALUE = "monthWise"


def wait_for_x_axis(page, timeout=30000):
    """
    Wait until #xAxis exists and the Month Wise option
    is actually present.
    """

    print("[*] Waiting for X-Axis dropdown and Month Wise option...")

    page.wait_for_function(
        """
        () => {
            const select = document.querySelector("#xAxis");

            if (!select) {
                return false;
            }

            const option = Array.from(select.options).find(
                o => o.value === "monthWise"
            );

            return !!option;
        }
        """,
        timeout=timeout,
        polling=200
    )

    print("[+] X-Axis dropdown contains Month Wise")


def select_x_axis(page):
    """
    Select Month Wise after the website has populated
    the X-Axis dropdown.
    """

    wait_for_x_axis(page, timeout=30000)

    print("[*] Selecting X-Axis = Month Wise")

    # Re-query the element immediately before selection
    x_axis = page.locator("#xAxis")

    x_axis.wait_for(
        state="visible",
        timeout=10000
    )

    x_axis.select_option(
        value="monthWise"
    )

    # Give the site's change handler a moment
    page.wait_for_timeout(500)

    actual_value = x_axis.input_value()

    print(
        f"[*] X-Axis current value: '{actual_value}'"
    )

    if actual_value == "monthWise":
        print("[+] X-Axis successfully selected: Month Wise")
        return True

    print(
        "[!] X-Axis selection was reset."
    )

    # Retry once
    page.wait_for_timeout(1000)

    x_axis = page.locator("#xAxis")

    x_axis.select_option(
        value="monthWise"
    )

    page.wait_for_timeout(500)

    actual_value = x_axis.input_value()

    print(
        f"[*] X-Axis after retry: '{actual_value}'"
    )

    if actual_value == "monthWise":
        print("[+] X-Axis successfully selected on retry")
        return True

    return False


def select_y_axis(page):

    print("[*] Waiting for Y-Axis...")

    y_axis = page.locator("#yAxis")
    y_axis.wait_for(
        state="visible",
        timeout=30000
    )

    # First reset Y-Axis to empty
    print("[*] Resetting Y-Axis to default...")
    y_axis.select_option(value="")
    page.wait_for_timeout(500)

    # Select the Y-Axis value
    print(
        f"[*] Selecting Y-Axis: {Y_AXIS_VALUE}"
    )
    y_axis.select_option(
        value=Y_AXIS_VALUE
    )
    page.wait_for_timeout(500)

    # Click the Y-Axis dropdown to trigger X-Axis population
    print("[*] Clicking Y-Axis dropdown to trigger X-Axis...")
    y_axis.click()
    page.wait_for_timeout(500)

    actual_value = y_axis.input_value()

    print(
        f"[*] Y-Axis current value: '{actual_value}'"
    )

    if actual_value != Y_AXIS_VALUE:

        print("[!] Y-Axis selection did not stick.")
        print("[*] Retrying...")

        y_axis.select_option(value="")
        page.wait_for_timeout(300)
        y_axis.select_option(
            value=Y_AXIS_VALUE
        )
        page.wait_for_timeout(300)
        y_axis.click()
        page.wait_for_timeout(500)

        actual_value = y_axis.input_value()

    if actual_value != Y_AXIS_VALUE:
        raise RuntimeError(
            f"Y-Axis selection failed. "
            f"Expected '{Y_AXIS_VALUE}', "
            f"got '{actual_value}'"
        )

    print("[+] Y-Axis successfully selected and triggered")


def print_x_axis_debug(page):
    """
    Print useful information about the X-Axis dropdown.
    """

    print("\n")
    print("=" * 70)
    print("X-AXIS DEBUG INFORMATION")
    print("=" * 70)

    try:

        debug = page.locator(
            "#xAxis"
        ).evaluate(
            """
            select => ({
                exists: true,
                value: select.value,
                selectedIndex: select.selectedIndex,

                selectedText:
                    select.options[select.selectedIndex]
                    ? select.options[select.selectedIndex].text
                    : null,

                optionCount: select.options.length,

                options:
                    Array.from(select.options).map(
                        option => ({
                            value: option.value,
                            text: option.text,
                            selected: option.selected
                        })
                    )
            })
            """
        )

        print(debug)

    except Exception as e:

        print(
            "[!] Could not inspect X-Axis:"
        )

        print(e)

    print("=" * 70)


def main():

    with sync_playwright() as p:

        print("[*] Starting browser...")

        browser = p.chromium.launch(
            headless=False,
            slow_mo=200
        )

        page = browser.new_page(
            viewport={
                "width": 1440,
                "height": 900
            }
        )

        # DIAGNOSTIC: log xhr/fetch/document AND script loads this time -
        # the previous filter excluded scripts, so we never actually saw
        # which page-specific JS file owns the Y-Axis/X-Axis logic.
        def _log_request(req):
            if req.resource_type in ("xhr", "fetch", "document", "script"):
                print(f"    -> request: {req.method} {req.url}")

        def _log_response(res):
            if res.request.resource_type in ("xhr", "fetch", "document", "script"):
                print(f"    <- response: {res.status} {res.url}")

        page.on("request", _log_request)
        page.on("response", _log_response)

        # DIAGNOSTIC: catch JS errors and console messages. The Y-Axis
        # onchange handler almost certainly runs client-side JS to rebuild
        # #xAxis's option list - if that handler throws partway through,
        # it would explain #xAxis losing its "monthWise" option with no
        # network call involved at all.
        page.on("console", lambda msg: print(f"    [console:{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: print(f"    [PAGE ERROR] {exc}"))

        try:

            # ========================================================
            # OPEN PAGE
            # ========================================================

            print(f"[*] Opening {URL}")

            page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            print("[+] Page opened")

            # Wait until Y-Axis exists
            page.locator(
                "#yAxis"
            ).wait_for(
                state="visible",
                timeout=15000
            )

            print("[+] Y-Axis found")

            # ========================================================
            # DIAGNOSTIC: list every <script src> on the page, so we can
            # identify which file actually contains the Y-Axis/X-Axis
            # rebuild logic (the generic vendor scripts like jquery/
            # bootstrap aren't it - we want the page-specific one).
            # ========================================================
            script_srcs = page.evaluate(
                """
                () => Array.from(document.querySelectorAll('script[src]'))
                    .map(s => s.src)
                """
            )
            print("[DIAG] <script src> tags on page:")
            for src in script_srcs:
                print(f"    {src}")

            # ========================================================
            # DIAGNOSTIC: scan window for any global var/function whose
            # name mentions "axis" - if the rebuild logic exposes a
            # reusable function or data map globally, this finds it so
            # we can potentially call it directly instead of relying on
            # the (apparently broken, in our automated context) onchange
            # trigger.
            # ========================================================
            axis_globals = page.evaluate(
                """
                () => Object.keys(window)
                    .filter(k => /axis/i.test(k))
                    .map(k => ({ key: k, type: typeof window[k] }))
                """
            )
            print(f"[DIAG] window keys matching /axis/i: {axis_globals}")

            # ========================================================
            # Y-AXIS
            # ========================================================

            select_y_axis(page)

            # ========================================================
            # Wait for X-Axis dropdown to be populated after Y-Axis change
            # The Y-Axis onchange triggers an AJAX call that rebuilds X-Axis options
            # ========================================================
            print("[*] Waiting for X-Axis to populate after Y-Axis selection...")
            page.wait_for_timeout(2500)

            # ========================================================
            # X-AXIS
            # ========================================================

            success = select_x_axis(page)

            if not success:

                print(
                    "\n[!] X-Axis could not be selected."
                )

                print_x_axis_debug(page)

                # Save screenshot for debugging
                page.screenshot(
                    path="x_axis_debug.png",
                    full_page=True
                )

                print(
                    "[+] Saved debugging screenshot:"
                    " x_axis_debug.png"
                )

                print(
                    "\nThe browser will remain open."
                )

                input(
                    "Press ENTER to close..."
                )

                return

            # ========================================================
            # CAPTCHA - Auto fill using OCR
            # ========================================================

            print("\n[*] Looking for CAPTCHA...")

            captcha_text = ""

            try:

                captcha = page.locator(
                    "#captchaImage"
                )

                captcha.wait_for(
                    state="visible",
                    timeout=10000
                )

                captcha.screenshot(
                    path="captcha.png"
                )

                print(
                    "[+] CAPTCHA saved to captcha.png"
                )

                # Try OCR extraction
                try:
                    from ocr_service import process_captcha
                    ocr_result = process_captcha("captcha.png")
                    print(f"[OCR] {ocr_result['message']}")
                    if ocr_result['is_valid']:
                        captcha_text = ocr_result['text']
                        print(f"[OCR] Extracted CAPTCHA text: {captcha_text}")
                except ImportError:
                    print("[!] ocr_service module not available. Install pytesseract and PIL.")
                except Exception as e:
                    print(f"[!] OCR extraction failed: {e}")

            except PWTimeoutError:

                print(
                    "[!] CAPTCHA image was not found."
                )

            # ========================================================
            # AUTO-FILL CAPTCHA
            # ========================================================

            if captcha_text:
                print("\n[*] Auto-filling CAPTCHA...")
                try:
                    captcha_input = page.locator("#externalCaptcha")
                    captcha_input.wait_for(state="visible", timeout=10000)
                    captcha_input.fill(captcha_text)
                    print(f"[+] CAPTCHA filled with: {captcha_text}")
                except Exception as e:
                    print(f"[!] Failed to fill CAPTCHA: {e}")
                    captcha_text = ""
            else:
                print("\n")
                print("=" * 70)
                print("MANUAL CAPTCHA REQUIRED")
                print("=" * 70)

                print(
                    "OCR failed. Enter the CAPTCHA manually in the browser."
                )

                print(
                    "Do not enter the CAPTCHA in this terminal."
                )

                print("=" * 70)

                input(
                    "\nPress ENTER after entering the CAPTCHA..."
                )

            # ========================================================
            # APPLY
            # ========================================================

            print("[*] Clicking Apply...")

            try:

                apply_button = page.locator(
                    "#applyTrigger"
                )

                apply_button.wait_for(
                    state="visible",
                    timeout=10000
                )

                apply_button.click()

                print("[+] Apply clicked")

            except PWTimeoutError:

                print(
                    "[!] Could not click Apply automatically."
                )

                print(
                    "[!] Please click Apply manually."
                )

            # ========================================================
            # KEEP BROWSER OPEN
            # ========================================================

            print("\n")
            print("=" * 70)
            print("DONE")
            print("=" * 70)

            input(
                "Press ENTER to close the browser..."
            )

        except Exception as e:

            print("\n")
            print("=" * 70)
            print("ERROR")
            print("=" * 70)

            print(e)

            print("=" * 70)

            print(
                "\nBrowser will remain open for debugging."
            )

            input(
                "Press ENTER to close..."
            )

        finally:

            browser.close()

            print("[*] Browser closed.")


if __name__ == "__main__":
    main()