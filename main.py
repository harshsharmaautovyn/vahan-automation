from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from side_checkpoint import select_sub_category, select_state_filters, select_class_filters


URL = "https://analytics.parivahan.gov.in/analytics/vahanpublicreport"

Y_AXIS_VALUE = "vehicleMakerName"
X_AXIS_VALUE = "monthWise"

MAX_CAPTCHA_APPLY_ATTEMPTS = 5   # how many full captcha+apply cycles to try
MAX_OCR_RETRIES_PER_ATTEMPT = 3  # OCR retries within a single cycle


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


def extract_captcha_text(page):
    """
    Runs the OCR-extraction loop against the CURRENT captcha image and
    returns the extracted text, or "" if OCR couldn't confidently read it.
    Does not click Apply. Does not fill the input.
    """

    captcha_text = ""
    retry_count = 0

    try:

        captcha_img = page.locator("#captchaImage")
        captcha_img.wait_for(
            state="visible",
            timeout=10000
        )

        retry_captcha_button = page.locator("#captchaImg")

        while retry_count < MAX_OCR_RETRIES_PER_ATTEMPT and not captcha_text:
            retry_count += 1
            print(f"\n[*] CAPTCHA OCR attempt {retry_count}/{MAX_OCR_RETRIES_PER_ATTEMPT}...")

            # Save current CAPTCHA image
            captcha_img.screenshot(
                path="captcha.png"
            )

            print(
                "[+] CAPTCHA saved to captcha.png"
            )

            # Try OCR extraction
            try:
                from ocr_service import process_captcha
                ocr_result = process_captcha("captcha.png")

                if not isinstance(ocr_result, dict) or "is_valid" not in ocr_result:
                    print(
                        f"[!] ocr_service returned an unexpected shape: {ocr_result!r}"
                    )
                elif ocr_result['is_valid']:
                    captcha_text = ocr_result['text']
                    print(f"[OCR] {ocr_result.get('message', '')}")
                    print(f"[OCR] Extracted CAPTCHA text: {captcha_text}")
                else:
                    print(f"[OCR] {ocr_result.get('message', 'Invalid CAPTCHA text')}, retrying...")
                    if retry_count < MAX_OCR_RETRIES_PER_ATTEMPT:
                        old_image = captcha_img.screenshot()

                        retry_captcha_button.click()

                        for _ in range(20):
                            page.wait_for_timeout(500)
                            new_image = captcha_img.screenshot()
                            if new_image != old_image:
                                break

            except ImportError as e:
                print(f"[!] ocr_service module not available/importable: {e}")
                print("[!] Install its dependencies (e.g. pytesseract, PIL) or fix the import path.")
                break

            except Exception:
                import traceback
                print("[!] OCR extraction call raised an exception:")
                traceback.print_exc()
                if retry_count < MAX_OCR_RETRIES_PER_ATTEMPT:
                    old_image = captcha_img.screenshot()

                    retry_captcha_button.click()

                    for _ in range(20):
                        page.wait_for_timeout(500)
                        new_image = captcha_img.screenshot()
                        if new_image != old_image:
                            break




        if not captcha_text:
            print(
                f"[!] CAPTCHA OCR extraction failed after {MAX_OCR_RETRIES_PER_ATTEMPT} attempts."
            )

    except PWTimeoutError:

        print(
            "[!] CAPTCHA image was not found."
        )

    return captcha_text


def fill_captcha(page, captcha_text):
    """
    Fills the captcha input. Falls back to manual entry if captcha_text
    is empty or the fill fails. Returns True once something is in the box.
    """

    if captcha_text:
        print("\n[*] Auto-filling CAPTCHA...")
        try:
            captcha_input = page.locator("#externalCaptcha")
            captcha_input.wait_for(state="visible", timeout=10000)
            captcha_input.clear()
            captcha_input.fill(captcha_text)
            print(f"[+] CAPTCHA filled with: {captcha_text}")
            return True
        except Exception as e:
            print(f"[!] Failed to fill CAPTCHA: {e}")

    print("\n")
    print("=" * 70)
    print("MANUAL CAPTCHA REQUIRED")
    print("=" * 70)

    print(
        "OCR failed (or auto-fill failed). Enter the CAPTCHA manually in the browser."
    )

    print(
        "Do not enter the CAPTCHA in this terminal."
    )

    print("=" * 70)

    input(
        "\nPress ENTER after entering the CAPTCHA..."
    )

    return True


def click_apply(page):
    """
    Clicks the Apply button. Returns True if the click itself succeeded
    (this says nothing about whether the captcha was actually correct -
    that's checked separately by check_apply_success).
    """

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
        return True

    except PWTimeoutError:

        print(
            "[!] Could not click Apply automatically."
        )

        print(
            "[!] Please click Apply manually."
        )

        return False


def check_apply_success(page, timeout=8000):
    """
    Uses the site's own CAPTCHA error indicator instead of guessing:

        <div class="alert alert-danger p-0">
            <span id="captchaMsg">Invalid CAPTCHA.</span>
        </div>

    This block only becomes visible when the submitted CAPTCHA was wrong.
    So: if #captchaMsg is visible after Apply -> failed, retry.
        if it's not visible -> succeeded, stop.
    """

    try:
        try:
            page.wait_for_load_state("networkidle", timeout=timeout)
        except PWTimeoutError:
            page.wait_for_timeout(min(timeout, 2500))

        try:
            captcha_msg = page.locator("#captchaMsg")
            is_visible = captcha_msg.is_visible(timeout=1500)
        except Exception:
            is_visible = False

        if is_visible:
            msg_text = ""
            try:
                msg_text = captcha_msg.inner_text().strip()
            except Exception:
                pass
            print(f"[!] CAPTCHA error shown on page: '{msg_text or 'Invalid CAPTCHA.'}'")
            return False

        print("[+] No CAPTCHA error shown - treating Apply as successful.")
        return True

    except Exception as e:
        print(f"[!] Error while checking Apply result: {e}")
        return False


def run_captcha_apply_cycle(page):
    """
    One full cycle: extract captcha -> fill -> click Apply -> check result.
    Returns True if the cycle appears to have succeeded.
    """

    captcha_text = extract_captcha_text(page)
    fill_captcha(page, captcha_text)
    click_apply(page)

    return check_apply_success(page)


def get_fresh_captcha(page):
    print("[DEBUG] Entered get_fresh_captcha")

    captcha_img = page.locator("#captchaImage")
    refresh_btn = page.locator("#captchaImg")

    # Capture the current image bytes
    old_image = captcha_img.screenshot()
    print("[DEBUG] Captured old captcha")

    # Trigger refresh using JavaScript (avoids Playwright waiting)
    refresh_btn.evaluate("el => el.click()")
    print("[DEBUG] Refresh button clicked")

    # Wait until the image pixels actually change
    for i in range(20):
        page.wait_for_timeout(500)
        new_image = captcha_img.screenshot()

        if new_image != old_image:
            print(f"[DEBUG] Captcha changed after {i+1} checks")
            return

        print(f"[DEBUG] Still waiting... {i+1}/20")

    raise RuntimeError("CAPTCHA image never changed after refresh.")


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


            # select_passenger_filters(page)
            select_state_filters(page)
            select_sub_category(page)
            select_class_filters(page)

            # ========================================================
            # CAPTCHA + APPLY - retry the whole cycle until it succeeds
            # ========================================================

            apply_succeeded = False
            attempt = 0

            while attempt < MAX_CAPTCHA_APPLY_ATTEMPTS and not apply_succeeded:
                attempt += 1

                print("\n")
                print("=" * 70)
                print(f"CAPTCHA + APPLY CYCLE {attempt}/{MAX_CAPTCHA_APPLY_ATTEMPTS}")
                print("=" * 70)

                apply_succeeded = run_captcha_apply_cycle(page)

                if not apply_succeeded and attempt < MAX_CAPTCHA_APPLY_ATTEMPTS:
                    print("[!] Cycle failed. Getting a fresh CAPTCHA and retrying...")
                    print("[*] Refreshing captcha...")
                    get_fresh_captcha(page)
                    print("[*] Starting next OCR cycle...")

            if not apply_succeeded:
                print("\n")
                print("=" * 70)
                print(f"GAVE UP after {MAX_CAPTCHA_APPLY_ATTEMPTS} attempts")
                print("=" * 70)
                print(
                    "Automatic captcha+apply retries were exhausted. "
                    "You can finish manually in the browser."
                )

            # ========================================================
            # KEEP BROWSER OPEN
            # ========================================================

            print("\n")
            print("=" * 70)
            print("DONE" if apply_succeeded else "STOPPED (manual finish needed)")
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