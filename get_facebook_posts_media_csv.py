import requests
import json
import csv
import argparse
import os
from dotenv import dotenv_values
from datetime import datetime


# Default arguments
default_ouput_filename = "output/facebook_page_media.csv"

# Constants
facebook_post_date_format = "%Y-%m-%dT%H:%M:%S%z"
facebook_access_token_env_name = "FB_PAGE_ACCESS_TOKEN"
facebook_page_post_ids_endpoint = "https://graph.facebook.com/v20.0/page_id/posts?fields=id&access_token=fb_access_token"
facebook_page_post_details_endpoint = "https://graph.facebook.com/v20.0/post_id?fields=id,created_time,permalink_url,attachments&access_token=fb_access_token"
facebook_page_album_ids_endpoint = "https://graph.facebook.com/v20.0/page_id/albums?fields=id&access_token=fb_access_token"
facebook_page_photos_endpoint = "https://graph.facebook.com/v20.0/entity_id/photos?fields=id,page_story_id,created_time,name,alt_text,images,link,height,width&access_token=fb_access_token"
supported_types = [
    'album',
    'photo',
    'cover_photo',
    'profile_media',
    'animated_image_autoplay',
    'video',
    'video_inline',
    'video_autoplay',
    'music',
]


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


def extract_attachments(node, field):
    if node is None:
        return []

    node_list = []
    node_list.append(node)

    if field in node and 'data' in node[field]:
        for entry in node[field]["data"]:
            node_list.extend(extract_attachments(entry, field))

    return node_list


def process_post_chunk(post_ids, facebook_access_token):
    processed_media = []

    for post_id in post_ids:
        details_url = facebook_page_post_details_endpoint.replace('post_id', post_id["id"]).replace('fb_access_token', facebook_access_token)
        post = get_request(details_url)
        
        post_time = post["created_time"]
        parsed_date = datetime.strptime(post_time, facebook_post_date_format)
        post["created_unix_timestamp"] = parsed_date.timestamp()

        if 'attachments' in post and 'data' in post["attachments"]:
            post_attachments = []

            for attachment in post["attachments"]["data"]:
                post_attachments.extend(extract_attachments(attachment, "subattachments"))

            for attachment in post_attachments:
                attachment_type = None
                attachment_target = dict()
                attachment_media_url = None
                attachment_title = None
                attachment_description = None
                error = None

                try:
                    attachment_type = attachment["type"]
                    if attachment_type not in supported_types:
                        continue

                    if 'title' in attachment:
                        attachment_title = f"{attachment["title"].replace("\n", " ")},"

                    if 'description' in attachment:
                        attachment_description = f"{attachment["description"].replace("\n", " ")},"

                    attachment_target = attachment.get("target")
                    attachment_media = attachment.get("media")

                    if attachment_target is None:
                        attachment_target = dict()

                    if attachment_media is not None:
                        attachment_media_url = attachment_media.get("source")
                        if attachment_media_url is None and attachment_media.get("image") is not None:
                            attachment_media_url = attachment_media["image"].get("src")
                
                except Exception as e: 
                    error = str(e)

                processed_media.append({
                    "id": post["id"],
                    "created_time": post["created_time"],
                    "created_unix_timestamp": post["created_unix_timestamp"],
                    "permalink_url": post["permalink_url"],
                    "media_id": attachment_target.get("id"),
                    "media_page_url": attachment_target.get("url"),
                    "media_title": attachment_title,
                    "media_description": attachment_description,
                    "media_type": attachment_type,
                    "media_url": attachment_media_url,
                    "error": error
                })

    return processed_media


def process_photo_chunk(photo_chunk):
    processed_media = []

    for photo in photo_chunk:
        title = None
        description = None
        actual_media = None
        error = None

        try:
            if 'name' in photo:
                title = f"{photo["name"].replace("\n", " ")},"

            if 'alt_text' in photo:
                description = f"{photo["alt_text"].replace("\n", " ")},"

            parsed_date = datetime.strptime(photo["created_time"], facebook_post_date_format)
            photo["created_unix_timestamp"] = parsed_date.timestamp()

            actual_media, = filter(lambda image: image["width"] == photo["width"] and image["height"] == photo["height"], photo["images"])

        except Exception as e: 
            error = str(e)

        processed_media.append({
            "id": photo["page_story_id"],
            "created_time": photo["created_time"],
            "created_unix_timestamp": photo.get("created_unix_timestamp"),
            "permalink_url": photo["link"],
            "media_id": photo["id"],
            "media_page_url": photo["link"],
            "media_title": title,
            "media_description": description,
            "media_type": "photo",
            "media_url": actual_media.get("source"),
            "error": error
        })
        
    return processed_media


def process_album_chunk(album_ids, facebook_access_token):
    processed_media = []

    for album_id in album_ids:
        photos_url = facebook_page_photos_endpoint.replace('entity_id', album_id["id"]).replace('fb_access_token', facebook_access_token)

        while photos_url is not None and photos_url != '':
            page = get_request(photos_url)

            chunk = page['data']
            processed_media.extend(process_photo_chunk(chunk))

            photos_url = page['paging'].get('next') if 'paging' in page else None

    return processed_media


def main():
    parser = argparse.ArgumentParser(description="Extract media information from posts and photo albums of a Facebook page.", )
    parser.add_argument(
        "--page_id",
        type=str,
        help="Facebook page's ID.",
        required=True,
    )
    parser.add_argument(
        "--output_filename",
        type=str,
        help="The output CSV file containing all attachment info of the posts.",
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

    data = {}

    # Iterating over Facebook posts
    cursor_url = facebook_page_post_ids_endpoint.replace('page_id', page_id).replace('fb_access_token', facebook_access_token)
    try:
        while cursor_url is not None and cursor_url != '':
            page = get_request(cursor_url)

            chunk = page['data']
            processed_media = process_post_chunk(chunk, facebook_access_token)
            for media in processed_media:
                data[f"{media["media_id"]}_{media["created_unix_timestamp"]}"] = media

            cursor_url = page['paging'].get('next')

    except requests.exceptions.RequestException as e:
        print(f"Failed to GET {cursor_url}: {e}")
        return 1

    except Exception as e:
        print(f"An error occurred while getting Facebook posts: {e}")
        return 1

    # Adding profile photos (assuming PAGE_ID as an album)
    processed_media = process_album_chunk([{"id": page_id}], facebook_access_token)
    for media in processed_media:
        data[f"{media["media_id"]}_{media["created_unix_timestamp"]}"] = media

    # Iterating over albums
    cursor_url = facebook_page_album_ids_endpoint.replace('page_id', page_id).replace('fb_access_token', facebook_access_token)
    try:
        while cursor_url is not None and cursor_url != '':
            page = get_request(cursor_url)

            chunk = page['data']
            processed_media = process_album_chunk(chunk, facebook_access_token)
            for media in processed_media:
                data[f"{media["media_id"]}_{media["created_unix_timestamp"]}"] = media

            cursor_url = page['paging'].get('next')

    except requests.exceptions.RequestException as e:
        print(f"Failed to GET {cursor_url}: {e}")
        return 1

    except Exception as e:
        print(f"An error occurred while getting albums: {e}")
        return 1

    data = list(data.values())
    data.sort(key=lambda post: post["created_unix_timestamp"])

    try:
        with open(output_filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "id",
                "created_time",
                "created_unix_timestamp",
                "permalink_url",
                "media_id",
                "media_page_url",
                "media_title",
                "media_description",
                "media_type",
                "media_url",
                "error"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for info in data:
                writer.writerow(info)

    except Exception as e:
        print(f"An error ocurred when trying to write to ouput file {output_filename}: {e}")
        return 1

    print(f"Process finished (number of media posts extracted: {len(data)}). Check out your file at {output_filename}!")

    return 0


if __name__ == "__main__":
    main()
