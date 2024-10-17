# EFPM

Acronym for *Extract Facebook Post Media* (I couldn't bring a joke this time...). It's a set of Python scripts to extract basic information from your Facebook page posts.

## Features

* Summarize your Facebook posts into a CSV file
* Download all your Facebook posts media you have posted

## Requirements

* Python 3.10
* Modules in `requirements.txt` (version may vary though)
* Experience using terminal/console
* Access to Meta Graph API

## First steps

### Facebook page ID

This one is easy. Go to your Facebook page, get into **About** section and click **Page transparency**. Here, copy the number shown as **Page ID** for later.

### Access to Meta Graph API

Before starting, note that this section may vary overtime, so I encourage you to review the official [Meta App Development docs](https://developers.facebook.com/docs/development).

The process is basically as follows:

1. [**Register**](https://developers.facebook.com/docs/development/register) with the account that have access to your Facebook page (is a must).
2. [**Create an App**](https://developers.facebook.com/docs/development/create-an-app). This may sound hard, but it's as simple as clicking some few buttons. **Important to note here, though**: When you are asked to select an use case, make sure to select *Other -> Business*.
3. Once you are in your app dashboard, click over **Tools** in the navbar, and then select **Graph API Explorer**.

### Getting a Facebook page Access Token

**Note**: I know this is just a possible (and maybe *unprofessional*) way to get the token, but this will do.

1. In the **Graph API Explorer**, go to the **Permissions** section at the right panel, and select the following two:
   * `pages_show_list`
   * `pages_read_engagement`
2. Click on **Generate Access Token**. This is going to ask you which page to access through your app.
3. **Select the page whose posts you want to get**. Then, accept the access request by clicking **Save** and **Got it**.
4. Finally, in **User or Page** field select your Facebook page.
5. Copy the **Access Token** generated at the very beginning of the panel.

Note that this token **expires after some time**, maybe that's enough for your case though. To refresh the token,

1. Click **Generate Access Token**.
2. Click **Reconnect** in the pop up window (this time it's not asking for permissions).
3. Select your Facebook page in **User or Page** field again.

### Setting token into project

For the first time, copy the contents of `.env.template` to create a new one called `.env`. Here, you'll see something like the following:

```bash
FB_PAGE_ACCESS_TOKEN=PASTE-YOUR-FACEBOOK-PAGE-ACCESS-TOKEN-HERE
```

Afterwards, copy the generated Access Token from **Graph API Explorer** and paste it into the file, replacing the `PASTE-YOUR-FACEBOOK-PAGE-ACCESS-TOKEN-HERE` part.

## Commands

Assuming you've already [installed Python](https://www.python.org/downloads/), [configured a *venv*](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/), and installed the `requirements.txt` modules, you can run any of the following three scripts.

**Tip.** Whenever you are unsure how to run the commands, `-h` option will be your friend!

Now, it's time to bring your Facebook page ID, buddy!

### `get_facebook_posts_csv.py`

This script will collect very basic stuff, like `id`, `created_time`, `message` and `story`.

The complete command is the following:

```sh
py get_facebook_posts_csv.py --page_id <page_id> --output_filename <output_filename>
```

All argument default options are the following:

| Argument | Default value | Description |
| - | - | - |
| `page_id` | *required, provided by user* | Facebook page's ID. |
| `output_filename` | output/facebook_page_posts.csv | The output CSV file containing all info of the posts. |

### `get_facebook_posts_media_csv.py`

This script is similar to the previous one. However, this one is specialized in getting all your Facebook page's media ONLY. Contains data like `id`, `created_time`, `media_id`, `media_page_url`, `media_title`, `media_url`, etc.

Its arguments are basically the same as the previous command. So the complete command is the following:

```sh
py get_facebook_posts_media_csv.py --page_id <page_id> --output_filename <output_filename>
```

All argument default options are the following:

| Argument | Default value | Description |
| - | - | - |
| `page_id` | *required, provided by user* | Facebook page's ID. |
| `output_filename` | output/facebook_page_media.csv | The output CSV file containing all attachment info of the posts. |

**Note that this script won't download any media.**

### `download_media.py`

As you may deduce by the name, this script lets you download all type of media extracted in the previous script (`get_facebook_posts_media_csv.py`), so make sure to specify it accordingly. The complete command is the following:

```sh
py download_media.py --column_post_id <column_post_id> --column_created_unix_timestamp <column_created_unix_timestamp> --column_attachment_id <column_attachment_id> --column_attachment_type <column_attachment_type> --column_attachment_media_url <column_attachment_media_url> --input_filename <input_filename> --output_directory <output_directory>
```

All argument default options are the following:

| Argument | Default value | Description |
| - | - | - |
| `column_post_id` | id | The column name where the Facebook post ID is stored. |
| `column_created_unix_timestamp` | created_unix_timestamp | The column name where the Facebook post UNIX timestamp is stored. |
| `column_attachment_id` | media_id | The column name where the media ID is stored. |
| `column_attachment_type` | media_type | The column name where the media type is stored (necessary to determine if downloadable or not). |
| `column_attachment_media_url` | media_url | The column name where the media URL is stored. |
| `input_filename` | output/facebook_page_media.csv | The input CSV file containing the Facebook media attachments URLs. |
| `output_directory` | output/media/ | The ouput folder name which the media will be saved. |

Don't panic! If you are, indeed, using the `get_facebook_posts_media_csv.py` script output, the basic usage often will be the following:

```sh
py download_media.py --input_filename <input_filename> --output_directory <output_directory>
```

Pretty neat, right?

# Limits

* Only "regular" posts and profile pictures are retrived from `get_facebook_posts_csv.py`. I couldn't find a way to retrieve posts with `"timeline_visibility": "no timeline unit for this post"`.
* Some photos extracted from `get_facebook_posts_media_csv.py` are going to be repeated due to simplifications over album retrieval in the code.

# Notes

The result will contain posts ordered by its UNIX timestamp ascendingly.

If there's any error with the script or this README, let me know by opening an issue, or maybe just throw me a message at my Twitter profile!
