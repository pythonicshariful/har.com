from main import scrape_har_properties

properties = scrape_har_properties(
    county="Harris",
    max_price=35000,
    max_pages=5,
    acreage=False,
    residential=True,
    output_filename=None,
)
print(len(properties))