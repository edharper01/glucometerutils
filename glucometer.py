#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility to manage glucometers' data."""

__author__ = 'Diego Elio Pettenò'
__email__ = 'flameeyes@flameeyes.eu'
__copyright__ = 'Copyright © 2013-2017, Diego Elio Pettenò'
__license__ = 'MIT'

import argparse
import importlib
import inspect
import logging
import sys
import datetime
import os

from glucometerutils import common
from glucometerutils import exceptions

def main():
  if sys.version_info < (3, 2):
    raise Exception(
      'Unsupported Python version, please use at least Python 3.2')

  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(dest="action")

  parser.add_argument(
    '--driver', action='store', required=True,
    help='Select the driver to use for connecting to the glucometer.')
  parser.add_argument(
    '--device', action='store', required=False,
    help=('Select the path to the glucometer device. Some devices require this '
          'argument, others will try autodetection.'))

  parser.add_argument(
    '--vlog', action='store', required=False, type=int,
    help=('Python logging level. See the levels at '
          'https://docs.python.org/3/library/logging.html#logging-levels'))

  subparsers.add_parser(
    'help', help=('Display a description of the driver, including supported '
                  'features and known quirks.'))
  subparsers.add_parser(
    'info', help='Display information about the meter.')
  subparsers.add_parser(
    'zero', help='Zero out the data log of the meter.')

  parser_dump = subparsers.add_parser(
    'dump', help='Dump the readings stored in the device.')
  parser_dump.add_argument(
    '--unit', action='store', choices=common.VALID_UNITS,
    help='Select the unit to use for the dumped data.')
  parser_dump.add_argument(
    '--sort-by', action='store', default='timestamp',
    choices=common._ReadingBase._fields,
    help='Field to order the dumped data by.')
  parser_dump.add_argument(
    '--with-ketone', action='store_true', default=False,
    help='Enable ketone reading if available on the glucometer.')
  parser_dump.add_argument(
    '--to-file', action='store_true', default=False,
    help='Output results to a file yyyymmddhhmmss.csv')
  parser_dump.add_argument(
    '--output-folder', action='store', default='.', required=False,
    help='Control the location of the file output')

  
  parser_date = subparsers.add_parser(
    'datetime', help='Reads or sets the date and time of the glucometer.')
  parser_date.add_argument(
    '--set', action='store', nargs='?', const='now', default=None,
    help='Set the date rather than just reading it from the device.')

  args = parser.parse_args()

  logging.basicConfig(level=args.vlog)

  try:
    driver = importlib.import_module('glucometerutils.drivers.' + args.driver)
  except ImportError as e:
    logging.error(
      'Error importing driver "%s", please check your --driver parameter:\n%s',
      args.driver, e)
    return 1

  # This check needs to happen before we try to initialize the device, as the
  # help action does not require a --device at all.
  if args.action == 'help':
    print(inspect.getdoc(driver))
    return 0

  device = driver.Device(args.device)

  device.connect()
  device_info = device.get_meter_info()

  try:
    if args.action == 'info':
      try:
        time_str = device.get_datetime()
      except NotImplementedError:
        time_str = 'N/A'
      print("{device_info}Time: {time}".format(
        device_info=str(device_info), time=time_str))
    elif args.action == 'dump':
      unit = common.UNIT_MMOLL #args.unit
      if unit is None:
        unit = device_info.native_unit

      readings = device.get_readings()

      if not args.with_ketone:
        readings = (reading for reading in readings
                    if not isinstance(reading, common.KetoneReading))

      if args.sort_by is not None:
        readings = sorted(
          readings, key=lambda reading: getattr(reading, args.sort_by))

      if args.to_file:
        #filter out dates in the future
        readings = (reading for reading in readings
                    if not reading.timestamp > datetime.datetime.now())
                    
        outputfilename=args.output_folder + '/{:%Y%m%d%H%M%S}.csv'.format(datetime.datetime.now())
        outputfile = open(outputfilename,"w")
        outputfile.write("Some guy\r\n# 000000001\r\n")
        outputfile.write("ID	Time	Record Type	Historic Glucose (mmol/L)	Scan Glucose (mmol/L)	Non-numeric Rapid-Acting Insulin	")
        outputfile.write("Rapid-Acting Insulin (units)	Non-numeric Food	Carbohydrates (grams)	Non-numeric Long-Acting Insulin	")
        outputfile.write("Long-Acting Insulin (units)	Notes	Strip Glucose (mmol/L)	Ketone (mmol/L)	Meal Insulin (units)	")
        outputfile.write("Correction Insulin (units)	User Change Insulin (units)	Previous Time	Updated Time\r\n")
      
        rowid = 1
        for reading in readings:
          outputfile.write(str(rowid) + "\t")
          outputfile.write(reading.as_tsv(unit))
          outputfile.write("\r\n")
          rowid += 1
        outputfile.close()
        os.chmod(outputfilename, 0o777)
      else:
        for reading in readings:
          print(reading.as_csv(unit))
    elif args.action == 'datetime':
      if args.set == 'now':
        print(device.set_datetime())
      elif args.set:
        try:
          from dateutil import parser as date_parser
          new_date = date_parser.parse(args.set)
        except ImportError:
          logging.error(
            'Unable to import module "dateutil", please install it.')
          return 1
        except ValueError:
          logging.error('%s: not a valid date', args.set)
          return 1
        print(device.set_datetime(new_date))
      else:
        print(device.get_datetime())
    elif args.action == 'zero':
      confirm = input('Delete the device data log? (y/N) ')
      if confirm.lower() in ['y', 'ye', 'yes']:
        device.zero_log()
        print('\nDevice data log zeroed.')
      else:
        print('\nDevice data log not zeroed.')
        return 1
    else:
      return 1
  except exceptions.Error as err:
    print('Error while executing \'%s\': %s' % (args.action, str(err)))
    return 1

  device.disconnect()

if __name__ == "__main__":
    main()
