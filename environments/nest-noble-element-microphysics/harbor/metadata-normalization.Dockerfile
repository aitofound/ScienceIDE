# Close the metadata localization channel after every final-stage filesystem change.
RUN find /app -xdev \( -name '*.orig' -o -name '*.bak' -o -name '*.rej' \
        -o -name '*~' -o -name '__pycache__' -o -name '.pytest_cache' \) \
        -prune -exec rm -rf -- {} + \
 && find /app -xdev \( -type f -o -type d -o -type l \) \
        -exec touch -h -d '2000-01-01T00:00:00Z' {} +
