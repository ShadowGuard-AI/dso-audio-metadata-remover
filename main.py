import argparse
import logging
import os
import shutil
import sys
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wave import WAVE
from mutagen.id3 import ID3, ID3NoHeaderError
from mutagen.easyid3 import EasyID3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Remove metadata from audio files to protect privacy.")
    parser.add_argument("input_file", help="Path to the input audio file.")
    parser.add_argument("-o", "--output_file", help="Path to the output audio file. If not specified, overwrites the input file.")
    parser.add_argument("-k", "--keep", nargs='+', help="List of tags to keep (e.g., title artist). All other tags will be removed.")
    parser.add_argument("-l", "--log_file", help="Path to the log file. If not specified, logs to console.")

    return parser.parse_args()


def remove_metadata(input_file, output_file=None, keep_tags=None):
    """
    Removes metadata from the specified audio file.

    Args:
        input_file (str): Path to the input audio file.
        output_file (str, optional): Path to the output audio file. If None, overwrites the input file. Defaults to None.
        keep_tags (list, optional): List of tags to keep. Defaults to None.
    """

    try:
        # Determine file type and load metadata
        if input_file.lower().endswith(".mp3"):
            try:
                audio = MP3(input_file, ID3=EasyID3)  #Handles ID3 v1, v1.1, and v2 tags
            except ID3NoHeaderError:
                 logging.warning(f"No ID3 header found in {input_file}.  Skipping metadata removal.")
                 return "no_metadata"
            file_type = "mp3"
        elif input_file.lower().endswith(".flac"):
            audio = FLAC(input_file)
            file_type = "flac"
        elif input_file.lower().endswith(".wav"):
            audio = WAVE(input_file)
            file_type = "wav"
        else:
            raise ValueError("Unsupported file format. Supported formats: MP3, FLAC, WAV")

        # Handle output file
        if output_file is None:
            output_file = input_file

        # For a separate output, copy the audio data there first and
        # strip the copy, so the output is a complete audio file and
        # the input is left untouched.
        if os.path.abspath(output_file) != os.path.abspath(input_file):
            if file_type == "wav":
                # Check for ID3 tags before copying, so a no tag run
                # does not leave an unstripped copy behind.
                try:
                    ID3(input_file)
                except ID3NoHeaderError:
                    logging.warning(f"No ID3 tags found in {input_file}.")
                    return "no_metadata"
            shutil.copyfile(input_file, output_file)
            if file_type == "mp3":
                audio = MP3(output_file, ID3=EasyID3)
            elif file_type == "flac":
                audio = FLAC(output_file)

        # Metadata removal logic
        if file_type == "mp3":
            if keep_tags:
                tags_to_remove = [tag for tag in audio.keys() if tag not in keep_tags]
            else:
                tags_to_remove = list(audio.keys())

            for tag in tags_to_remove:
                try:
                  del audio[tag]
                except KeyError:
                  logging.warning(f"Tag '{tag}' not found in {input_file}, skipping.")
                except Exception as e:
                  logging.error(f"Error deleting tag '{tag}' from {input_file}: {e}")
                  raise

        elif file_type == "flac":
            if keep_tags:
                tags_to_remove = [tag for tag in audio.keys() if tag not in keep_tags]
            else:
                tags_to_remove = list(audio.keys())

            for tag in tags_to_remove:
                try:
                    del audio[tag]
                except KeyError:
                    logging.warning(f"Tag '{tag}' not found in {input_file}, skipping.")
                except Exception as e:
                    logging.error(f"Error deleting tag '{tag}' from {input_file}: {e}")
                    raise


        elif file_type == "wav":
            # WAV files might not always have metadata stored in a standard way.
            #  We can try to remove ID3 tags if they exist.  This might not be comprehensive.
             try:
                  audio_id3 = ID3(output_file)
                  if keep_tags:
                      for tag in list(audio_id3.keys()):
                          if tag not in keep_tags:
                              del audio_id3[tag]
                      audio_id3.save(output_file)
                  else:
                      audio_id3.delete()
                  logging.info(f"ID3 tags removed from {output_file}")
             except ID3NoHeaderError:
                  logging.info(f"No ID3 tags found in {input_file}.")
                  return "no_metadata"
             except Exception as e:
                  logging.error(f"Error while removing ID3 tags from {output_file}: {e}")
                  raise
            # mutagen WAVE doesn't directly expose a key-value store for metadata like MP3/FLAC, so
            # targeted removal is harder without more format-specific parsing.

        # Save the modified audio file
        if file_type != "wav": #WAV saves handled differently
            try:
               audio.save(output_file)
               logging.info(f"Metadata removed from {input_file} and saved to {output_file}")
            except Exception as e:
               logging.error(f"Error saving file {output_file}: {e}")
               raise
        else:
            logging.info(f"ID3 metadata removed from {output_file}.")
        return "removed"

    except FileNotFoundError:
        logging.error(f"File not found: {input_file}")
        raise
    except ValueError as e:
        logging.error(str(e))
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise

def main():
    """
    Main function to parse arguments and call the metadata removal function.
    """
    args = setup_argparse()

    # Configure logging to file if specified
    if args.log_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)


    try:
        if args.keep:
            result = remove_metadata(args.input_file, args.output_file, args.keep)
        else:
            result = remove_metadata(args.input_file, args.output_file)
        if result == "no_metadata":
            print(f"No metadata found in {args.input_file}.")
            if args.output_file:
                sys.exit(1)
            return
        print("Metadata removal complete.")

    except Exception as e:
       print(f"Error: {e}")
       sys.exit(1)


if __name__ == "__main__":
    # Example usage:
    # 1. Remove all metadata from input.mp3, overwriting the file:
    #    python main.py input.mp3
    # 2. Remove all metadata from input.flac and save to output.flac:
    #    python main.py input.flac -o output.flac
    # 3. Remove all metadata from input.wav, overwriting the file:
    #    python main.py input.wav
    # 4. Keep only the title and artist tags:
    #    python main.py input.mp3 -k title artist
    # 5. Log to a file:
    #    python main.py input.mp3 -l audio_metadata_remover.log
    main()