import os
import time
import pandas as pd
from datetime import datetime
import logging


"""
This class provides the functionality to load trajectory data into 
cBLUE.  Currently, the sbet files are expected to be ASCII files
that are exported from Applanix's PosPac software.  
"""


class Sbet:
    def __init__(self, sbet_dir):
        """
        The data from all of the loaded sbet files are represented by
        a single Sbet object.  When the Sbet class is instantiated,
        the sbet object does not contain any sbet data.  The data
        are "loaded" (assigned to a field of the sbet object) when
        the user clicks the 'Load Sbet Data' button.
        :param str sbet_dir: directory contained trajectory files
        """
        self.sbet_dir = sbet_dir
        self.sbet_files = sorted(['{}\{}'.format(sbet_dir, f) for f in os.listdir(sbet_dir)
                                  if f.endswith('.txt')])
        self.data = None
        self.SECS_PER_GPS_WK = 7 * 24 * 60 * 60  # 604800 sec
        self.SECS_PER_DAY = 24 * 60 * 60  # 86400 sec
        self.GPS_EPOCH = datetime(1980, 1, 6, 0, 0, 0)
        self.GPS_ADJUSTED_OFFSET = 1e9

    @staticmethod
    def get_sbet_date(sbet):
        """parses year, month, and day from ASCII sbet filename

        :param str sbet: ASCII sbet filename
        :return: List[int]
        """
        sbet_parts = sbet.split('\\')
        sbet_name = sbet_parts[-1]
        year = int(sbet_name[0:4])
        month = int(sbet_name[4:6])
        day = int(sbet_name[6:8])
        sbet_date = [year, month, day]
        return sbet_date

    def gps_sow_to_gps_adj(self, gps_date, gps_wk_sec):
        """converts GPS seconds-of-week timestamp to GPS adjusted standard time

        In the case that the timestamps in the sbet files are GPS week seconds,
        this method is called to convert the timestamps to GPS adjusted standard
        time, which is what the las file timestamps are.  The timestamps in the
        sbet and las files need to be the same format, because the merging process
        merges the data in the sbet and las files based on timestamps.

        :param ? gps_date: [year, month, day]
        :param ? gps_wk_sec: GPS seconds-of-week timestamp
        :return: float
        """
        
        logging.info('converting GPS week seconds to GPS adjusted standard time...'),

        year = gps_date[0]
        month = gps_date[1]
        day = gps_date[2]

        sbet_date = datetime(year, month, day)
        dt = sbet_date - self.GPS_EPOCH
        gps_wk = int((dt.days * self.SECS_PER_DAY + dt.seconds) / self.SECS_PER_GPS_WK)
        gps_time = gps_wk * self.SECS_PER_GPS_WK + gps_wk_sec
        gps_time_adj = gps_time - self.GPS_ADJUSTED_OFFSET

        return gps_time_adj

    def check_if_sow(self, time):
        logging.info('checking if timestamps are SOW...')
        if time <= self.SECS_PER_GPS_WK:
            return True
        else:
            return False

    def build_sbets_data(self):
        """builds 1 pandas dataframe from all ASCII sbet files

        :return: pandas dataframe

        The following table lists the contents of the returned pandas sbet dataframe:

        =====   =============================================================
        Index   description
        =====   =============================================================
        0       timestamp (GPS seconds-of-week or GPS standard adjusted time)
        1       longitude
        2       latitude
        3       X (easting)
        4       Y (northing)
        5       Z (ellipsoid height)
        6       roll
        7       pitch
        8       heading
        9       standard deviation X
        10      standard deviation Y
        11      standard deviation Z
        12      standard deviation roll
        13      standard deviation pitch
        14      standard deviation heading
        =====   =============================================================
        """

        sbets_df = pd.DataFrame()
        header_sbet = ['time', 'lon', 'lat', 'X', 'Y', 'Z', 'roll', 'pitch', 'heading',
                       'stdX', 'stdY', 'stdZ', 'stdroll', 'stdpitch', 'stdheading']
        for sbet in sorted(self.sbet_files):
            logging.info('-' * 50)
            logging.info('getting trajectory data from {}...'.format(sbet))
            sbet_df = pd.read_table(
                sbet,
                skip_blank_lines=True,
                engine='c',
                delim_whitespace=True,
                header=None,
                names=header_sbet,
                index_col=False)
            logging.info('({} trajectory points)'.format(sbet_df.shape[0]))
            sbet_date = self.get_sbet_date(sbet)

            is_sow = self.check_if_sow(sbet_df['time'][0])
            if is_sow:
                gps_time_adj = self.gps_sow_to_gps_adj(sbet_date, sbet_df['time'])
                sbet_df['time'] = gps_time_adj

            sbets_df = sbets_df.append(sbet_df, ignore_index=True)

        sbets_data = sbets_df.sort_values(['time'], ascending=[1])

        return sbets_data

    def set_data(self):
        """populates Sbet object's data field with pandas dataframe (when user
        presses the "Load Trajectory File(s)" button)

        :return: n/a
        """
        sbet_tic = time.clock()
        self.data = self.build_sbets_data()  # df
        sbet_toc = time.clock()
        logging.info('It took {:.1f} mins to load the trajectory data.'.format((sbet_toc - sbet_tic) / 60))

    def get_tile_data(self, north, south, east, west):
        """queries the sbet data points that lie within the given las tile bounding coordinates

        One pandas dataframe is created from all of the loaded ASCII sbet files,
        but as each las tile is processed, only the sbet data located within the
        las tile limits are sent to the calc_tpu() method.

        :param float north: northern limit of las tile
        :param float south: southern limit of las tile
        :param float east: eastern limit of las tile
        :param float west: western limit of las tile
        :return: pandas dataframe
        """
        data = self.data[(self.data.Y >= south) & (self.data.Y <= north) &
                         (self.data.X >= west) & (self.data.X <= east)]

        return data


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
    sbet = Sbet(r'C:\QAQC_contract\marco_island')
    sbet_df = sbet.build_sbets_data()
    print(sbet_df)