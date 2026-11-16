import os
import re

"""After copying the files from the docker machine, run this to fix the URLs."""
directory = "static_version"

# Define URL patterns to update
url_patterns = [
    "anonymous/",
    "antiquarian/",
    "bibliography/",
    "citing-author/",
    "citing-work/",
    "fragment/",
    "testimonium/",
    "topic/",
    "work/",
]

new_prefix = "frrant-static/"  # Based on the repo name

# Regex to find URLs that match the patterns and end with / but don't have index.html
url_regex = re.compile(
    r"(/(?:"
    + "|".join(re.escape(pattern) for pattern in url_patterns)
    + r')[^"\']*/)(?!index\.html)(?=["\'])'
)

# Regex to find URLs starting with / that don't have the prefix
prefix_regex = re.compile(r'(?<=href="/)(?!{re.escape(new_prefix)})([^"\']*)')


def update_html_files(directory):
    for subdir, _, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith(".html"):
                file_path = os.path.join(subdir, file_name)

                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()

                # Add prefix to URLs starting with /
                content = prefix_regex.sub(new_prefix + r"\1", content)

                # Add index.html to end of URLs that match patterns and end with /
                updated_content = url_regex.sub(r"\1index.html", content)

                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(updated_content)

                print(f"Updated {file_path}")


if __name__ == "__main__":
    update_html_files(directory)
