import aiohttp
import asyncio
import sys
import os
from datetime import datetime

# Reconfigure system output encoding
sys.stdout.reconfigure(encoding='utf-8')

# Initialize variables
base_url = ""
folder_base_url = ""

# Define the headers for the API request
headers = {
    "User-Agent": "Mobile",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en",
    "api-version": "51"
}

def set_token(token):
    global base_url, folder_base_url
    base_url = f'https://api.classplusapp.com/v2/course/preview/content/list/{token}?limit=1000&offset=0'
    folder_base_url = f'https://api.classplusapp.com/v2/course/preview/content/list/{token}?limit=1000&offset=0'

# Function to get folder name and IDs
async def get_folders(session, folder_id=None):
    try:
        url = folder_base_url if folder_id is None else f'{folder_base_url}&folderId={folder_id}'
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            folder_data = await response.json()
            folder_list = folder_data.get('data', [])
            return {folder['id']: folder['name'] for folder in folder_list}
    except aiohttp.ClientResponseError as http_err:
        print(f"HTTP error occurred while fetching folders: {http_err}")
    except ValueError as json_err:
        print(f"JSON Decode Error while fetching folders: {json_err}")
    except Exception as err:
        print(f"An error occurred while fetching folders: {err}")
    return {}

# Function to get course content for a specific folder
async def get_course_content(session, folder_id):
    try:
        url = f'{base_url}&folderId={folder_id}'
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    except aiohttp.ClientResponseError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except ValueError as json_err:
        print(f"JSON Decode Error: {json_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return None

# Function to filter and display name and modify thumbnailUrl
def filter_content(content, folder_path):
    filtered_content = []
    if content and isinstance(content, dict):
        items = content.get('data', [])
        for item in items:
            if isinstance(item, dict):
                name = item.get('name')
                thumbnailurl = item.get('thumbnailUrl')
                if thumbnailurl and 'thumbnail.png' in thumbnailurl:
                    thumbnailurl = thumbnailurl.replace('thumbnail.png', 'master.m3u8')  # Replace part of the URL
                if name and thumbnailurl:
                    # Add multiple conditions to check the thumbnailurl
                    if 'drm/wv' in thumbnailurl:
                        new_url_parts = thumbnailurl.replace('drm/wv/', 'drm/').split('/')
                        if len(new_url_parts) > 6:
                            new_url = "/".join(new_url_parts[:5] + new_url_parts[6:])  # Remove the 6th part
                            thumbnailurl = new_url
                    elif 'cpvi' in thumbnailurl:
                        new_url = thumbnailurl.replace('cpvideocdn.testbook.com/streams/', 'cpvod.testbook.com/')
                        new_url = new_url.replace('/master.m3u8', '/playlist.m3u8')
                        thumbnailurl = new_url
                    elif 'tencent' in thumbnailurl and 'thumbnail.jpg' in thumbnailurl:
                        new_url = thumbnailurl.replace('media-cdn.classplusapp.com/tencent', 'tencdn.classplusapp.com').replace('thumbnail.jpg', 'master.m3u8')
                        thumbnailurl = new_url
                    elif 'snapshots/' in thumbnailurl:
                        parts = thumbnailurl.split('/')
                        if len(parts) > 5:
                            # Adjust the URL as per the specified pattern
                            new_url = f"https://media-cdn.classplusapp.com/alisg-cdn-a.classplusapp.com/{parts[5]}/master.m3u8"
                            thumbnailurl = new_url

                    elif '4b06bf8d61c41f8310af9b2624459378203740932b456b07fcf817b737fbae27' in thumbnailurl:
                        new_url_parts = thumbnailurl.split('/')
                        if len(new_url_parts) > 1:
                            new_url = f'https://media-cdn-a.classplusapp.com/mig-01/b08bad9ff8d969639b2e43d5769342cc62b510c4345d2f7f153bec53be84fe35/{new_url_parts[-1]}/{new_url_parts[-1]}.m3u8'
                            new_url = new_url.replace('.jpeg', '')
                            thumbnailurl = new_url
                    elif 'pdf' in thumbnailurl:
                        thumbnailurl = thumbnailurl
                    elif '/1d' in thumbnailurl:
                        thumbnailurl = 'URL not available'
                    elif 'media-cdn.classplusapp.com' in thumbnailurl and 'thumbnail.png' in thumbnailurl and 'cc' in thumbnailurl and 'lc' in thumbnailurl:
                        new_url = thumbnailurl.replace('thumbnail.png', 'master.m3u8')
                        thumbnailurl = new_url
                    elif 'cdn-wl-assets.classplus.co/production/single' in thumbnailurl:
                        thumbnailurl = 'URL not available'
                    elif 'cc' in thumbnailurl or 'lc' in thumbnailurl:
                        # Add new condition for 'cc' and 'lc' in thumbnailurl
                        new_url = thumbnailurl.replace('thumbnail.png', 'master.m3u8')
                        thumbnailurl = new_url 
                    else:
                        print(f"Media CDN URL: {thumbnailurl}")

                    filtered_content.append({'folder_path': folder_path, 'name': name, 'thumbnailurl': thumbnailurl})
            else:
                print(f"Skipping item: {item}, it is not a dictionary.")
    return filtered_content

# Recursive function to fetch and print content for all folders
async def process_folder(session, folder_id, folder_path, file, indent=0):
    content = await get_course_content(session, folder_id)
    if content:
        filtered_content = filter_content(content, folder_path)
        if filtered_content:
            for item in filtered_content:
                if item['name'] and item['thumbnailurl']:  # Condition to check if both name and thumbnailurl exist
                    output = f"{' ' * indent}{folder_path} - {item['name']} : {item['thumbnailurl']}\n"
                    print(output.strip())
                    file.write(output)
    else:
        output = f"{' ' * indent}Failed to retrieve course content for {folder_path}.\n"
        print(output.strip())
        file.write(output)

    subfolders = await get_folders(session, folder_id)
    if subfolders:
        tasks = [
            process_folder(session, subfolder_id, folder_path + " " + subfolder_name, file, indent + 2)
            for subfolder_id, subfolder_name in subfolders.items()
        ]
        await asyncio.gather(*tasks)

async def generate_content_file(msg):
    async with aiohttp.ClientSession() as session:
        folders = await get_folders(session)

        file_name = "batch_content.txt"
        with open(file_name, 'w', encoding='utf-8') as file:
            if folders:
                tasks = [
                    process_folder(session, folder_id, folder_name, file)
                    for folder_id, folder_name in folders.items()
                ]
                await asyncio.gather(*tasks)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_file_name = f"batch_content_{timestamp}.txt"
        os.rename(file_name, new_file_name)

        if os.path.getsize(new_file_name) > 0:
            return new_file_name
        else:
            return None
