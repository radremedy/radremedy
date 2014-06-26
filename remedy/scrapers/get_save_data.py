from howardbrown import HowardBrownScraper
import json

# TODO: save to database
data = HowardBrownScraper().scrape()

print(data)
