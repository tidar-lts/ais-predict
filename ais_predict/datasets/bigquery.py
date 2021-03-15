import geopandas as gpd
import pandas as pd
from google.cloud import bigquery, bigquery_storage
import google.auth
from shapely.geometry.polygon import Polygon
import shapely.wkt

def download(limit: int = 1000, lead=0, within: Polygon=None, mmsi: list = None, project_id: str="master-thesis-305112" ,credentials=None) -> gpd.GeoDataFrame:
    """Creates a query job in Bigquery and downloades the result into a GeoPandas Dataframe
    

    Keyword Arguments:
    limit -- number of results to include. None returns all results.
    within -- coordinate filter, only points within the this polygon is included. None returns all results.
    mmsi -- list-like containing mmsi values to include in the result. None returns all.
    credentials -- google cloud credentials object. None use the google.auth.default.
    project_id -- google cloud project id to use for billing.
    """

    if credentials is None:
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
    
    # Make clients.
    bq = bigquery.Client(credentials=credentials, project=project_id,)
    bqstorage = bigquery_storage.BigQueryReadClient(credentials=credentials)
    lead += 1
    limit = "LIMIT " + str(limit) if limit else ""
    within = f"AND ST_WITHIN(sample_0.position, ST_GEOGFROMTEXT('{str(within)}'))" if within else ""
    mmsi = "'" + "','".join(mmsi) + "'" if mmsi else None
    mmsi = f"AND CAST(mmsi AS STRING) IN ({mmsi})" if mmsi else ""

    # Select samples
    query = f"SELECT mmsi"
    for l in range(lead):
        query += f", sample_{l}.* "
    query += f"FROM `master-thesis-305112.ais.samples_with_lead`"

    # Filter out bad samples
    query += "WHERE TRUE"
    for l in range(lead):
        query += f" AND sample_{l}.timestamp IS NOT NULL "
        if l > 0:
            query += f"AND TIMESTAMP_DIFF(sample_{l}.timestamp, sample_{l-1}.timestamp, MINUTE) < 30"
    
    # Additional filters
    query += f"""
                {within}
                {mmsi}
                ORDER BY mmsi, sample_0.timestamp
                {limit}
             """
    df = bq.query(query).result().to_dataframe(bqstorage_client=bqstorage)

    # Convert timestamps and positions to correct dtypes
    df.position = gpd.GeoSeries.from_wkt(df.position, crs="wgs84")
    df.timestamp = pd.to_datetime(df.timestamp)
    for l in range(1, lead):
        df[f"position_{l}"] = gpd.GeoSeries.from_wkt(df[f"position_{l}"], crs="wgs84")
        df[f"timestamp_{l}"] = pd.to_datetime(df[f"timestamp_{l}"])
    df = gpd.GeoDataFrame(df, geometry="position")
    return df