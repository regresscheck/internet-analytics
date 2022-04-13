class last_element_changed:
    def __init__(self, locator, last_element):
        self.locator = locator
        self.last_element = last_element

    def __call__(self, driver):
        elements = driver.find_elements(*self.locator)
        # TODO: handle no elements better
        assert len(elements) != 0
        if elements[-1] != self.last_element:
            return elements[-1]
        else:
            return False
