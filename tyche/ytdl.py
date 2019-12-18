import datetime
import discord
import functools
import youtube_dl


async def create_ytdl_source(voice, url, *, ytdl_options=None, **kwargs):
    """|coro|
    Creates a stream source for youtube or other services that launches
    in a separate thread to play the audio.
    The source uses the ``youtube_dl`` python library to get the information
    required to get audio from the URL. Since this uses an external library,
    you must install it yourself. You can do so by calling
    ``pip install youtube_dl``.
    You must have the ffmpeg or avconv executable in your path environment
    variable in order for this to work.
    The operations that can be done on the source are the same as those in
    :meth:`create_stream_player`. The source has been augmented and enhanced
    to have some info extracted from the URL. If youtube-dl fails to extract
    the information then the attribute is ``None``. The ``yt``, ``url``, and
    ``download_url`` attributes are always available.
    +---------------------+---------------------------------------------------------+
    |      Operation      |                       Description                       |
    +=====================+=========================================================+
    | source.yt           | The `YoutubeDL <ytdl>` instance.                        |
    +---------------------+---------------------------------------------------------+
    | source.url          | The URL that is currently playing.                      |
    +---------------------+---------------------------------------------------------+
    | source.download_url | The URL that is currently being downloaded to ffmpeg.   |
    +---------------------+---------------------------------------------------------+
    | source.title        | The title of the audio stream.                          |
    +---------------------+---------------------------------------------------------+
    | source.description  | The description of the audio stream.                    |
    +---------------------+---------------------------------------------------------+
    | source.uploader     | The uploader of the audio stream.                       |
    +---------------------+---------------------------------------------------------+
    | source.upload_date  | A datetime.date object of when the stream was uploaded. |
    +---------------------+---------------------------------------------------------+
    | source.duration     | The duration of the audio in seconds.                   |
    +---------------------+---------------------------------------------------------+
    | source.likes        | How many likes the audio stream has.                    |
    +---------------------+---------------------------------------------------------+
    | source.dislikes     | How many dislikes the audio stream has.                 |
    +---------------------+---------------------------------------------------------+
    | source.is_live      | Checks if the audio stream is currently livestreaming.  |
    +---------------------+---------------------------------------------------------+
    | source.views        | How many views the audio stream has.                    |
    +---------------------+---------------------------------------------------------+
    .. _ytdl: https://github.com/rg3/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L128-L278
    Examples
    ----------
    Basic usage: ::
        voice = await channel.connect()
        source = await create_ytdl_source(voice, 'https://www.youtube.com/watch?v=d62TYemN6MQ')
        source.start()
    Parameters
    -----------
    url : str
        The URL that ``youtube_dl`` will take and download audio to pass
        to ``ffmpeg`` or ``avconv`` to convert to PCM bytes.
    ytdl_options : dict
        A dictionary of options to pass into the ``YoutubeDL`` instance.
        See `the documentation <ytdl>`_ for more details.
    \*\*kwargs
        The rest of the keyword arguments are forwarded to
        :func:`create_ffmpeg_player`.
    Raises
    -------
    ClientException
        Popen failure from either ``ffmpeg``/``avconv``.
    Returns
    --------
    StreamPlayer
        An augmented StreamPlayer that uses ffmpeg.
        See :meth:`create_stream_player` for base operations.
    """
    use_avconv = kwargs.get("use_avconv", False)
    opts = {"format": "webm[abr>0]/bestaudio/best", "prefer_ffmpeg": not use_avconv}

    if ytdl_options is not None and isinstance(ytdl_options, dict):
        opts.update(ytdl_options)

    ydl = youtube_dl.YoutubeDL(opts)
    func = functools.partial(ydl.extract_info, url, download=False)
    info = await voice.loop.run_in_executor(None, func)
    if "entries" in info:
        info = info["entries"][0]

    print("playing URL {}".format(url))
    download_url = info["url"]
    source = discord.FFmpegPCMAudio(download_url)
    if source.is_opus():
        print("Cannot enable volume, source is Opus")
    else:
        # Wrap in volume-adjuster:
        source = discord.PCMVolumeTransformer(source)

    # set the dynamic attributes from the info extraction
    source.download_url = download_url
    source.url = url
    source.yt = ydl
    source.views = info.get("view_count")
    source.is_live = bool(info.get("is_live"))
    source.likes = info.get("like_count")
    source.dislikes = info.get("dislike_count")
    source.duration = info.get("duration")
    source.uploader = info.get("uploader")

    is_twitch = "twitch" in url
    if is_twitch:
        # twitch has 'title' and 'description' sort of mixed up.
        source.title = info.get("description")
        source.description = None
    else:
        source.title = info.get("title")
        source.description = info.get("description")

    # upload date handling
    date = info.get("upload_date")
    if date:
        try:
            date = datetime.datetime.strptime(date, "%Y%M%d").date()
        except ValueError:
            date = None

    source.upload_date = date
    return source
