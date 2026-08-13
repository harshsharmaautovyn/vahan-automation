STATE_FILTERS = [
    "All",
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


def select_state_filters(page):
    """
    Select the required State filters from the State multiselect.
    Currently selects: All
    """

    print("[*] Selecting State filters...")

    # Get only the State dropdown
    dropdown = page.locator(
        ".multiselect-dropdown",
        has=page.locator("span.placeholder", has_text="Select State")
    )

    # Open it once
    dropdown.click(force=True)

    # Wait for this dropdown's list
    dropdown.locator(".multiselect-dropdown-list-wrapper").wait_for(
        state="visible",
        timeout=5000
    )

    for item in STATE_FILTERS:
        print(f"    Selecting: {item}")

        if item.upper() == "ALL":
            option = dropdown.locator(".multiselect-dropdown-all-selector")
        else:
            option = dropdown.locator(
                f'div[data-search-text="{item.upper()}"]'
            )

        option.wait_for(state="visible", timeout=5000)

        checkbox = option.locator("input[type='checkbox']")

        if not checkbox.is_checked():
            checkbox.check(force=True)

    print("[+] State filters selected")


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

