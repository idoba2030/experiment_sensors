import os

def get_image_files(folder='images', valid_exts=('.jpeg', '.jpg', '.png', '.bmp', '.gif')):
    """
    Returns a sorted list of image filenames in the specified folder,
    matching the given valid extensions.
    
    :param folder: path to the images directory (default='images')
    :param valid_exts: tuple/list of valid file extensions
    :return: a sorted list of filenames (strings)
    """
    # Get a list of everything in the folder
    all_files = os.listdir(folder)
    
    # Filter to only include files with valid extensions
    image_files = [
        f for f in all_files
        if os.path.splitext(f)[1].lower() in valid_exts
    ]
    
    # Sort the list for consistency
    image_files.sort()
    
    return image_files
