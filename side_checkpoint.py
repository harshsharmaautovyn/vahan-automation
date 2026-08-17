STATE_FILTERS = [
    "Andaman & Nicobar Island",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chhattisgarh",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu & Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Lakshadweep",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "UT of DNH and DD",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
]

SUB_CATEGORY_FILTERS = [
    "FOUR WHEELER (Invalid Carriage)",
    "LIGHT MOTOR VEHICLE",
    "LIGHT PASSENGER VEHICLE",
]

CLASS_FILTERS = [
    "ADAPTED VEHICLE",
    "MOTOR CAB",
    "MOTOR CAR",
]


def select_single_state(page, state_name):
    print(f"[*] Selecting only: {state_name}")

    page.evaluate("""
    stateName => {
        const select = document.querySelector('#stateName');
        if (!select) throw new Error('stateName select not found');

        Array.from(select.options).forEach(option => {
            option.selected = option.text.trim() === stateName;
        });

        select.dispatchEvent(new Event('change', { bubbles: true }));
        select.dispatchEvent(new Event('input', { bubbles: true }));
    }
    """, state_name)

    page.wait_for_timeout(700)



def unselect_single_state(page, state_name):
    print(f"[*] Unselecting state: {state_name}")

    dropdown = page.locator(
        ".multiselect-dropdown",
        has=page.locator("span.placeholder", has_text="Select State")
    )

    dropdown.click(force=True)

    option = dropdown.locator(
        f'div[data-search-text="{state_name.upper()}"]'
    )

    checkbox = option.locator("input[type='checkbox']")

    if checkbox.is_checked():
        checkbox.uncheck(force=True)

    dropdown.click(force=True)
    page.wait_for_timeout(500)



def select_state_filters(page):
    print("[*] Selecting all states...")

    page.evaluate("""
    () => {
        const select = document.querySelector('#stateName');
        Array.from(select.options).forEach(o => o.selected = true);

        select.dispatchEvent(new Event('change', { bubbles: true }));
        select.dispatchEvent(new Event('input', { bubbles: true }));
    }
    """)

    page.wait_for_timeout(700)


def double_click_all_state(page):
    print("[*] Resetting State dropdown (All -> All)...")

    print("1 - About to find dropdown")

    dropdown = page.locator(
        ".multiselect-dropdown",
        has=page.locator("span.placeholder", has_text="Select State")
    )

    print("2 - Dropdown found, about to click")

    dropdown.evaluate("el => el.click()")

    print("3 - Dropdown clicked")

    page.wait_for_timeout(300)

    all_option = page.locator(".multiselect-dropdown-all-selector")

    print("4 - All option found, first click")

    all_option.evaluate("el => el.click()")

    print("5 - First click done")

    page.wait_for_timeout(300)

    print("6 - Second click")

    all_option.evaluate("el => el.click()")

    print("7 - Second click done")

    page.wait_for_timeout(300)

    print("8 - Closing dropdown")

    page.keyboard.press("Escape")

    print("9 - Finished")

    page.wait_for_timeout(300)


def reset_state_dropdown(page):
    print("[*] Clearing state selection...")

    page.evaluate("""
    () => {
        const select = document.querySelector('#stateName');
        Array.from(select.options).forEach(o => o.selected = false);

        select.dispatchEvent(new Event('change', { bubbles: true }));
        select.dispatchEvent(new Event('input', { bubbles: true }));
    }
    """)

    page.wait_for_timeout(500)



def select_sub_category(page):
    """
    Select the required Sub-Category values using the hidden select element.
    """

    print("[*] Selecting Passenger Sub-Category filters...")

    page.evaluate(
        """
        values => {
            const select = document.querySelector('#vehicleSubCategory');
            if (!select) throw new Error('vehicleSubCategory not found');

            Array.from(select.options).forEach(option => {
                option.selected = values.includes(option.value);
            });

            select.dispatchEvent(new Event('change', { bubbles: true }));
            select.dispatchEvent(new Event('input', { bubbles: true }));
        }
        """,
        SUB_CATEGORY_FILTERS
    )

    page.wait_for_timeout(1000)

    print("[+] Passenger Sub-Category filters selected")



def select_class_filters(page):
    """
    Select the required Class filters from the Class multiselect.
    """

    print("[*] Selecting Class filters...")

    # Get the custom dropdown that belongs to #vehicleClass
    dropdown = page.locator(
        "#vehicleClass + .multiselect-dropdown"
    )

    # Open it
    dropdown.click(force=True)

    # Wait for THIS dropdown to open
    dropdown.locator(".multiselect-dropdown-list-wrapper").wait_for(
        state="visible",
        timeout=5000
    )

    for item in CLASS_FILTERS:
        print(f"    Selecting: {item}")

        option = dropdown.locator(
            f'div[data-search-text="{item}"]'
        )

        option.wait_for(state="visible", timeout=5000)

        checkbox = option.locator("input[type='checkbox']")

        if not checkbox.is_checked():
            option.click(force=True)
            page.wait_for_timeout(300)

    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    print("[+] Class filters selected")

