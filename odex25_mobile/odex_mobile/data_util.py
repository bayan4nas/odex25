class DataUtil:

    def generateLink(self, pager):
        """
            Extract [next_page] [prev_page] from odoo website pager class
        """
        prev = self.page_item_link(pager, 'page_previous')
        nxt = self.page_item_link(pager, 'page_next')
        page = self.page_item_link(pager, 'page')
        links = {
            'prev': None if prev == nxt or prev == page else prev,
            'next':  None if prev == nxt or nxt == page else nxt,
        }
        return links

    def page_item_link(self, pager, key):
        """
            Extract url from link object
        """
        data = pager.get(key)
        return data.get('url')


data_util = DataUtil()
