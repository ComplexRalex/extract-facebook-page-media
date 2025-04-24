import argparse
import pandas as pd
import requests
import os
from urllib.parse import urlparse, unquote
from datetime import datetime


# Default arguments
default_column_post_id = "id"
default_column_created_unix_timestamp = "created_unix_timestamp"
default_column_attachment_id = "media_id"
default_column_attachment_type = "media_type"
default_column_attachment_media_url = "media_url"
default_input_filename = "output/facebook_page_media.csv"
default_output_directory = "output/media/"

# Constants
supported_formats = [
    "jpeg",
    "jpg",
    "png",
    "mp3",
    "mp4"
] # TODO missings?
accepted_types = [
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
custom_date_format = "%Y-%m-%d_%H.%M.%S"


def verify_directory(output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    return


def get_filename_from_url(url):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)

    return unquote(filename)


def get_media_format(filename):
    *_, extension = filename.split(".")

    return extension


def download_file(url, save_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return False

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description='Download media files from the generated Facebook posts attachments file (only those with media URL).')
    parser.add_argument(
        '--column_post_id',
        type=str,
        help='The column name where the Facebook post ID is stored.',
        default=default_column_post_id
    )
    parser.add_argument(
        '--column_created_unix_timestamp',
        type=str,
        help='The column name where the Facebook post UNIX timestamp is stored.',
        default=default_column_created_unix_timestamp
    )
    parser.add_argument(
        '--column_attachment_id',
        type=str,
        help='The column name where the media ID is stored.',
        default=default_column_attachment_id
    )
    parser.add_argument(
        '--column_attachment_type',
        type=str,
        help='The column name where the media type is stored (necessary to determine if downloadable or not).',
        default=default_column_attachment_type
    )
    parser.add_argument(
        '--column_attachment_media_url',
        type=str,
        help='The column name where the media URL is stored.',
        default=default_column_attachment_media_url
    )
    parser.add_argument(
        '--input_filename',
        type=str,
        help='The input CSV file containing the Facebook media attachments URLs.',
        default=default_input_filename
    )
    parser.add_argument(
        '--output_directory',
        type=str,
        help='The ouput folder name which the media will be saved.',
        default=default_output_directory
    )

    args = parser.parse_args()

    column_post_id = args.column_post_id
    column_created_unix_timestamp = args.column_created_unix_timestamp
    column_attachment_id = args.column_attachment_id
    column_attachment_type = args.column_attachment_type
    column_attachment_media_url = args.column_attachment_media_url
    csv_media_file = args.input_filename
    output_directory = args.output_directory
    
    verify_directory(output_directory)

    dataframe = pd.read_csv(csv_media_file)

    successful_downloads = 0
    for index, row in dataframe.iterrows():
        attachment_type = row[column_attachment_type]
        if attachment_type not in accepted_types:
            continue

        attachment_media_url = row.get(column_attachment_media_url)
        if attachment_media_url is None:
            continue

        post_id = row[column_post_id]
        created_unix_timestamp = row[column_created_unix_timestamp]
        attachment_id = row[column_attachment_id]

        parsed_date = datetime.fromtimestamp(created_unix_timestamp)
        post_formatted_date = parsed_date.strftime(custom_date_format)

        actual_filename = get_filename_from_url(attachment_media_url)
        extension = get_media_format(actual_filename)
        if extension.lower() not in supported_formats:
            continue

        filename = f"{post_id} {attachment_id} {post_formatted_date}.{extension}"
        save_path = os.path.join(output_directory, filename)

        if download_file(attachment_media_url, save_path):
            print(f"[{post_id}][{index + 1}/{len(dataframe)}] Media {attachment_id} downloaded correctly: " + filename)
            successful_downloads += 1
        else:
            print(f"[{post_id}][{index + 1}/{len(dataframe)}] Couldn't download {attachment_id}...")

    print(f"Process finished. (number of attached media files extracted: {successful_downloads}). Check out your files at {output_directory}!")

    return 0


if __name__ == '__main__':
    main()
