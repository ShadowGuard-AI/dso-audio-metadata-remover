# dso-audio-metadata-remover
Command-line tool to remove metadata from audio files (MP3, WAV, FLAC, etc.) to protect privacy. Utilizes libraries like mutagen to access and remove ID3 tags and other metadata fields. - Focused on Tools for sanitizing and obfuscating sensitive data within text files and structured data formats

## Install
`git clone https://github.com/ShadowStrikeHQ/dso-audio-metadata-remover`

## Usage
`./dso-audio-metadata-remover [params]`

## Parameters
- `-h`: Show help message and exit
- `-o`: Path to the output audio file. If not specified, overwrites the input file.
- `-k`: No description provided
- `-l`: Path to the log file. If not specified, logs to console.

## License
Copyright (c) ShadowStrikeHQ
