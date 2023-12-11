import datetime
import requests  # This may need to be installed from pip
import yaml
import pinboard

with open("config.yml", "r") as file:
    config = yaml.safe_load(file)
readwise_token = config["READWISE_ACCESS_TOKEN"]
pinboard_token = config["PINBOARD_API_TOKEN"]
state_filename = config["STATE_FILE"]
try:
    with open(state_filename, "r") as file:
        updated_after = file.read().strip() or None
except FileNotFoundError:
    updated_after = None


def fetch_reader_document_list_api(updated_after=None, location=None):
    full_data = []
    next_page_cursor = None
    while True:
        params = {}
        if next_page_cursor:
            params["pageCursor"] = next_page_cursor
        if updated_after:
            params["updatedAfter"] = updated_after
        if location:
            params["location"] = location
        print("Making export api request with params " + str(params) + "...")
        response = requests.get(
            url="https://readwise.io/api/v3/list/",
            params=params,
            headers={"Authorization": f"Token {readwise_token}"},
        )
        full_data.extend(response.json()["results"])
        next_page_cursor = response.json().get("nextPageCursor")
        if not next_page_cursor:
            break
    return full_data


def add_article_to_pinboard(article):
    pb = pinboard.Pinboard(pinboard_token)
    pb.posts.add(
        url=article["source_url"],
        description=article["title"],
        extended=article["summary"],
        tags=list(article["tags"].keys()),
    )


# Get all of a user's archived documents
articles = fetch_reader_document_list_api(updated_after=updated_after, location="archive")
print(f"Fetched {len(articles)} articles")
count = 0
for article in articles:
    if article["source_url"].startswith("mailto:"):
        print(f"Skipping \"{article['title']}\" as it was an email newsletter.")
        continue
    if "noarchive" in article["tags"]:
        print(f"Skipping \"{article['title']}\" as it has the 'noarchive' tag..")
        continue
    add_article_to_pinboard(article)
    count += 1
print(f"Saved {count} articles to pinboard.")

with open(state_filename, "w") as file:
    file.write(datetime.datetime.now().isoformat())

print("Updated date in state file")
