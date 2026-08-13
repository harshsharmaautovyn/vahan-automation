"""
Vahan Public Report - form filler
==================================

Y-Axis:
    vehicleMakerName

X-Axis:
    monthWise / Month Wise

CAPTCHA:
    Manual entry only. No OCR or automatic solving.
"""

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError


URL = "https://analytics.parivahan.gov.in/analytics/vahanpublicreport"

Y_AXIS_VALUE = "vehicleMakerName"
X_AXIS_VALUE = "monthWise"


def wait_for_x_axis(page):
    """
    Wait until #xAxis exists and contains the Month Wise option.
    """

    print("[*] Waiting for X-Axis dropdown...")

    page.locator("#xAxis").wait_for(
        state="attached",
        timeout=20000
    )

    # Wait until Month Wise is actually present
    page.wait_for_function(
        """
        () => {
            const select = document.querySelector("#xAxis");

            if (!select) {
                return false;
            }

            return Array.from(select.options).some(
                option => option.value === "monthWise"
            );
        }
        """,
        timeout=2000
    )

    print("[+] X-Axis contains Month Wise")


def select_x_axis(page):
    """
    Select Month Wise and verify that the browser retained it.
    """

    print("[*] Selecting X-Axis = Month Wise")

    wait_for_x_axis(page)

    # Re-query the element immediately before selection.
    # This is important because the site may replace the select element.
    x_axis = page.locator("#xAxis")

    x_axis.select_option(
        value="monthWise"
    )

    # Allow any change event / JavaScript handler to execute
    page.wait_for_timeout(500)

    # Read actual selected value from the DOM
    actual_value = page.locator(
        "#xAxis"
    ).input_value()

    print(
        f"[*] X-Axis current value: '{actual_value}'"
    )

    if actual_value == "monthWise":
        print("[+] X-Axis successfully selected: Month Wise")
        return True

    # ------------------------------------------------------------
    # Retry using JavaScript DOM selection + change event
    # ------------------------------------------------------------

    print(
        "[!] Normal Playwright selection was not retained."
    )

    print(
        "[*] Trying JavaScript selection..."
    )

    result = page.locator("#xAxis").evaluate(
        """
        select => {
            const option = Array.from(select.options)
                .find(o => o.value === "monthWise");

            if (!option) {
                return {
                    success: false,
                    reason: "monthWise option not found"
                };
            }

            select.value = "monthWise";

            select.dispatchEvent(
                new Event("change", {
                    bubbles: true
                })
            );

            return {
                success: true,
                value: select.value,
                text: option.text
            };
        }
        """
    )

    print("[*] JavaScript selection result:")
    print(result)

    page.wait_for_timeout(1000)

    # Verify again
    actual_value = page.locator(
        "#xAxis"
    ).input_value()

    print(
        f"[*] X-Axis after JavaScript attempt: "
        f"'{actual_value}'"
    )

    if actual_value == "monthWise":
        print(
            "[+] X-Axis successfully selected: Month Wise"
        )
        return True

    return False


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

            print(
                f"[*] Selecting Y-Axis: "
                f"{Y_AXIS_VALUE}"
            )

            y_axis = page.locator("#yAxis")

            y_axis.select_option(
                value=Y_AXIS_VALUE
            )

            print(
                "[+] Y-Axis selected"
            )

            # Verify
            y_value = y_axis.input_value()

            print(
                f"[*] Y-Axis current value: "
                f"'{y_value}'"
            )

            if y_value != Y_AXIS_VALUE:

                raise RuntimeError(
                    "Y-Axis selection failed."
                )

            # ========================================================
            # IMPORTANT
            # ========================================================
            #
            # The website may now execute JavaScript that modifies
            # or completely replaces #xAxis.
            #
            # Instead of holding an old locator/reference, we wait
            # for the NEW DOM state and query #xAxis again.
            # ========================================================

            print(
                "[*] Waiting for Y-Axis JavaScript..."
            )

            page.wait_for_timeout(2000)

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
            # CAPTCHA
            # ========================================================

            print("\n[*] Looking for CAPTCHA...")

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

            except PWTimeoutError:

                print(
                    "[!] CAPTCHA image was not found."
                )

            # ========================================================
            # MANUAL CAPTCHA
            # ========================================================

            print("\n")
            print("=" * 70)
            print("MANUAL CAPTCHA REQUIRED")
            print("=" * 70)

            print(
                "Enter the CAPTCHA manually in the browser."
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