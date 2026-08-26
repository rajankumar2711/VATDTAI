from conftest import get_page


class BasePage:
    def __init__(self, get_page):
        self.page = get_page

    # This method is implemented to wait for a specific element
    def wait_for(self, locator):
        self.page.wait_for_selector(locator)

    # Wait for an element to be clickable
    def wait_for_element_clickable(self, selector):
        self.page.wait_for_selector(selector, state="visible")

    # Wait for an element to be visible by locator
    def wait_for_element_visible(self, selector):
        self.page.wait_for_selector(selector, state="visible")

    # Verify an element's existence with a timeout
    def verify_element_existence_with_timeout(self, selector, timeout):
        return self.page.wait_for_selector(selector, state="visible", timeout=timeout)

    # Wait for the invisibility of an element
    def wait_for_element_invisibility(self, selector):
        self.page.wait_for_selector(selector, state="hidden")

    # Verify invisibility of an element
    def verify_element_invisibility(self, selector):
         return self.page.is_hidden(selector)

    # Wait for page load
    def wait_for_page_load(self):
        self.page.wait_for_load_state("load")

    # This method is implemented to enter text
    def enter_text(self, locator, value):
        self.page.locator(locator).fill(value)

    # Clear text from an input element
    def clear_text(self, locator):
        self.page.fill(locator, "")

    # This method is implemented to click element
    def element_click(self, locator):
        self.page.locator(locator).click()

    # Double click an element
    def double_click(self, selector):
        self.page.dblclick(selector)

    # This method is implemented to select option from dropdown
    def select_dropdown_with_value(self, locator, value):
        self.page.locator(locator).select_option(value=value)

    # Get all dropdown options
    def get_dropdown_options(self, selector):
        options = self.page.query_selector_all(f"{selector} option")
        return [self.page.evaluate("option => option.textContent", option) for option in options]

    # Get the selected value from a dropdown
    def get_selected_dropdown_value(self, selector):
        selected_option = self.page.query_selector(f"{selector} option[selected]")
        return self.page.evaluate("option => option.value", selected_option)

    # This method is implemented to get text from a element
    def get_text(self, locator):
        return self.page.locator(locator).inner_text()

    # This method is implemented to verify if the input checkbox is checked
    def is_checked(self, locator):
        return self.page.locator(locator).is_checked()

    # Accept an alert dialog
    def accept_alert(self):
        self.page.on("dialog", lambda dialog: dialog.accept())

    # Dismiss an alert dialog
    def dismiss_alert(self):
        self.page.on("dialog", lambda dialog: dialog.dismiss())

    # Wait for an alert
    def wait_for_alert(self):
        self.page.wait_for_event("dialog")

    # Get text from an alert dialog
    def get_text_from_alert(self):
        global alert_text
        def handle_dialog(dialog):
            global alert_text
            alert_text = dialog.message
            dialog.accept()
        self.page.on("dialog", handle_dialog)
        return alert_text

    # Navigate to the previous page
    def navigate_back(self):
        self.page.go_back()

    # Navigate to the next page
    def navigate_forward(self):
        self.page.go_forward()

    # Refresh the current page
    def refresh_page(self):
        self.page.reload()

    # Navigate to a URL
    def navigate_to_url(self, url):
        self.page.goto(url)

    # Close the current window and switch to the parent window
    def close_page_and_switch(self, context):
        self.page.close()
        # Assuming you have a reference to the parent page
        return context.pages[0] if context.pages else None

    # Drag and drop an element
    def drag_and_drop(self, drag_selector, drop_selector):
        self.page.drag_and_drop(drag_selector, drop_selector)

    # Get a list of elements
    def get_elements(self, selector):
        return self.page.query_selector_all(selector)

    # Get an element's property value
    def get_element_property(self, selector, property_name):
        return self.page.get_attribute(selector, property_name)

    # Validate an element's text content
    def validate_element_text(self, selector, expected_text):
        actual_text = self.page.text_content(selector)
        return actual_text == expected_text

    # Verify the application title
    def verify_application_title(self, expected_title):
        return self.page.title() == expected_title

    # Verify the current URL
    def verify_current_url(self, expected_url):
        return self.page.url() == expected_url

    # Verify if an element is enabled
    def verify_element_enabled(self, selector):
        return self.page.is_enabled(selector)

    # Verify if an element is selected
    def verify_element_selected(self, selector):
        return self.page.is_checked(selector)

    # Verify tooltip text
    def verify_tooltip_text(self, selector, expected_tooltip_text):
        tooltip_text = self.page.get_attribute(selector, "title")
        return tooltip_text == expected_tooltip_text

    # Mouse hover
    def mouse_hover(self, selector):
        self.page.hover(selector)

    # Mouse hover and click
    def mouse_hover_and_click(self, selector):
        self.page.hover(selector)
        self.page.click(selector)