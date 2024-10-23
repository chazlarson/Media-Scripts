from tmdbapis import TMDbAPIs

def get_tmdb_item(tmdb_id, tvdb_id):
    tmdb_item = None

    if tmdb_id is None and tvdb_id is None:
        return tmdb_item

    if library_item.TYPE == "show":
        if tmdb_id is not None:
            logger((f"{item_title}: tmdb_id: {tmdb_id} - getting tv_show"), 'info', 'a')
            tmdb_item = tmdb.tv_show(tmdb_id)
            logger((f"{item_title}: tmdb_id: {tmdb_id} - FOUND {tmdb_item.title}"), 'info', 'a')
        else:
            logger((f"{item_title}: no tmdb_id, trying tvdb_id"), 'info', 'a')
            if tvdb_id is not None:
                logger((f"{item_title}: tvdb_id: {tvdb_id} - SEARCHING FOR tv_show"), 'info', 'a')
                tmdb_search = (
                    tmdb.find_by_id(tvdb_id=tvdb_id)
                )
                if len(tmdb_search.tv_results) > 0:
                    tmdb_item = tmdb_search.tv_results[0]
                    logger((f"{item_title}: tvdb_id: {tvdb_id} - FOUND {tmdb_item.title}"), 'info', 'a')
            else:
                logger((f"{item_title}: no tvdb_id specified"), 'info', 'a')


    else:
        if tmdb_id is not None:
            logger((f"{item_title}: tmdb_id: {tmdb_id} - getting movie"), 'info', 'a')
            tmdb_item = tmdb.movie(tmdb_id)
            logger((f"{item_title}: tmdb_id: {tmdb_id} - FOUND {tmdb_item.title}"), 'info', 'a')

    return tmdb_item
