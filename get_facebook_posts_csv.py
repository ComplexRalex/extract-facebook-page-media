import requests
import json
import csv
import argparse
import os
from dotenv import dotenv_values
from datetime import datetime


# Default arguments
default_ouput_filename = "output/facebook_page_posts.csv"

# Constants
facebook_post_date_format = "%Y-%m-%dT%H:%M:%S%z"
facebook_access_token_env_name = "FB_PAGE_ACCESS_TOKEN"
facebook_page_posts_endpoint = "https://graph.facebook.com/v20.0/page_id/feed?fields=id,message,story,created_time,permalink_url,is_published&access_token=fb_access_token"
facebook_page_photos_endpoint = "https://graph.facebook.com/v20.0/page_id/photos?fields=id,page_story_id&access_token=fb_access_token"
facebook_page_post_details_endpoint = "https://graph.facebook.com/v20.0/post_id?fields=id,message,story,created_time,permalink_url,is_published&access_token=fb_access_token"


def verify_directory(output_filename):
    output_directory = os.path.dirname(output_filename)

    if output_directory != '' and not os.path.exists(output_directory):
        os.makedirs(output_directory)

    return


def get_request(url):
    response = requests.get(url)
    response.raise_for_status()

    result = json.loads(response.text)

    return result


def process_post(post):
    post_message = post.get("message")
    if post_message is not None:
        post["message"] = f"{post_message.replace("\n", " ")},"

    post_story = post.get("story")
    if post_story is not None:
        post["story"] = f"{post_story.replace("\n", " ")},"

    post_time = post["created_time"]
    parsed_date = datetime.strptime(post_time, facebook_post_date_format)
    post["created_unix_timestamp"] = parsed_date.timestamp()

    return post


def process_post_chunk(posts):
    processed_posts = []

    for post in posts:
        processed_posts.append(process_post(post))

    return processed_posts


def process_photo_chunk(photos, facebook_access_token):
    processed_posts = []

    for photo in photos:
        details_url = facebook_page_post_details_endpoint.replace('post_id', photo["page_story_id"]).replace('fb_access_token', facebook_access_token)
        
        post = get_request(details_url)

        processed_posts.append(process_post(post))

    return processed_posts


def main():
    parser = argparse.ArgumentParser(description="Extract information from posts of a Facebook page.", )
    parser.add_argument(
        "--page_id",
        type=str,
        help="Facebook page's ID.",
        required=True,
    )
    parser.add_argument(
        "--output_filename",
        type=str,
        help="The output CSV file containing all info of the posts.",
        default=default_ouput_filename,
    )

    args = parser.parse_args()
    env_vars = dotenv_values(".env")

    if env_vars[facebook_access_token_env_name] is None:
        print(f"The Facebook access token is missing. Define it into an .env file as the following: {facebook_access_token_env_name}")
        return 1

    facebook_access_token = env_vars[facebook_access_token_env_name]
    page_id = args.page_id
    output_filename = args.output_filename

    verify_directory(output_filename)

    data = []

    # Iterating over Facebook page posts
    cursor_url = facebook_page_posts_endpoint.replace('page_id', page_id).replace('fb_access_token', facebook_access_token)
    try:
        while cursor_url is not None and cursor_url != '':
            page = get_request(cursor_url)

            chunk = page['data']
            data.extend(process_post_chunk(chunk))

            cursor_url = page['paging'].get('next')

    except requests.exceptions.RequestException as e:
        print(f"Failed to GET {cursor_url}: {e}")
        return 1

    except Exception as e:
        print(f"An error occurred while getting posts: {e}")
        return 1

    # Iterating over profile pictures
    cursor_url = facebook_page_photos_endpoint.replace('page_id', page_id).replace('fb_access_token', facebook_access_token)
    try:
        while cursor_url is not None and cursor_url != '':
            page = get_request(cursor_url)

            chunk = page['data']
            data.extend(process_photo_chunk(chunk, facebook_access_token))

            cursor_url = page['paging'].get('next')

    except requests.exceptions.RequestException as e:
        print(f"Failed to GET {cursor_url}: {e}")
        return 1

    except Exception as e:
        print(f"An error occurred while getting photo posts: {e}")
        return 1

    data = [dict(t) for t in {tuple(sorted(d.items())) for d in data}] # remove duplicates heh
    data.sort(key=lambda post: post["created_unix_timestamp"])

    try:
        with open(output_filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "id",
                "created_time",
                "created_unix_timestamp",
                "message",
                "story",
                "is_published",
                "permalink_url",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for info in data:
                writer.writerow(info)

    except Exception as e:
        print(f"An error ocurred when trying to write to ouput file {output_filename}: {e}")
        return 1

    print(f"Process finished (number of posts extracted: {len(data)}). Check out your file at {output_filename}!")

    return 0


if __name__ == "__main__":
    main()
