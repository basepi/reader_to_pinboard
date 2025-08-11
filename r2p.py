import datetime
import requests  # This may need to be installed from pip
import yaml
import pinboard
from pinboard.exceptions import PinboardServiceUnavailable, PinboardError
import sys



def fetch_reader_document_list_api(readwise_token, updated_after=None, location=None):
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
        #print("Making export api request with params " + str(params) + "...")
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


def add_article_to_pinboard(pb, article):
    try:
        pb.posts.add(
            url=article["source_url"],
            description=article["title"],
            extended=article["summary"],
            tags=list(article["tags"].keys()),
        )
    except PinboardServiceUnavailable:
        print(f"Pinboard is unavailable or rate limiting. Exiting.")
        sys.exit(1)
    except pinboard.exceptions.PinboardError as exc:
        print(f"Pinboard had an error, skipping \"{article['title']}\": {exc}")
        return

def run():
    # Print timestamp
    print(datetime.datetime.now(datetime.UTC).isoformat())
    # Read config
    with open("config.yml", "r") as file:
        config = yaml.safe_load(file)
    readwise_token = config["READWISE_ACCESS_TOKEN"]
    pinboard_token = config["PINBOARD_API_TOKEN"]
    state_filename = config["STATE_FILE"]
    beeminder_webhook = config["BEEMINDER_WEBHOOK"]
    pb = pinboard.Pinboard(pinboard_token)
    try:
        with open(state_filename, "r") as file:
            updated_after = file.read().strip() or None
            print(f"Statefile read, updated_after: {updated_after}")
    except FileNotFoundError:
        print("No statefile found. Aborting.")
        return
    # Get all of a user's archived documents
    articles = fetch_reader_document_list_api(readwise_token, updated_after=updated_after, location="archive")
    print(f"Fetched {len(articles)} articles")
    #print(articles)
    archived_count = 0
    read_count = 0
    for article in articles:
        read_count += 1
        if article["source_url"].startswith("mailto:"):
            print(f"Skipping \"{article['title']}\" as it was an email newsletter.")
            continue
        if "noarchive" in article["tags"]:
            print(f"Skipping \"{article['title']}\" as it has the 'noarchive' tag..")
            continue
        if not article["source_url"]:
            print(f"Skipping \"{article['title']}\" as it has no URL")
            continue
        add_article_to_pinboard(pb, article)
        archived_count += 1
    print(f"Saved {archived_count} articles to pinboard.")

    if read_count > 0:
        response = requests.post(beeminder_webhook, data={"read_count": read_count})
        print(f"Updated Beeminder with {read_count}, status code {response.status_code}")

    with open(state_filename, "w") as file:
        file.write(datetime.datetime.now(datetime.UTC).isoformat())

    print("Updated date in state file")


if __name__ == "__main__":
    run()
