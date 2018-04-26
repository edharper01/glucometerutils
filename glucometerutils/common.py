# -*- coding: utf-8 -*-
"""Common routines for data in glucometers."""

__author__ = 'Diego Elio Pettenò'
__email__ = 'flameeyes@flameeyes.eu'
__copyright__ = 'Copyright © 2013, Diego Elio Pettenò'
__license__ = 'MIT'

import collections
import enum
import textwrap

from glucometerutils import exceptions

class Unit(enum.Enum):
  MG_DL = 'mg/dL'
  MMOL_L = 'mmol/L'

# Constants for meal information
class Meal(enum.Enum):
  NONE = ''
  BEFORE = 'Before Meal'
  AFTER = 'After Meal'

# Constants for measure method
class MeasurementMethod(enum.Enum):
  BLOOD_SAMPLE = 'blood sample'
  CGM = 'CGM' # Continuous Glucose Monitoring


def convert_glucose_unit(value, from_unit, to_unit):
  """Convert the given value of glucose level between units.

  Args:
    value: The value of glucose in the current unit
    from_unit: The unit value is currently expressed in
    to_unit: The unit to conver the value to: the other if empty.

  Returns:
    The converted representation of the blood glucose level.
  """
  from_unit = Unit(from_unit)
  to_unit = Unit(to_unit)

  if from_unit == to_unit:
    return value

  if from_unit == Unit.MG_DL:
    return round(value / 18.0, 2)
  else:
    return round(value * 18.0, 0)

_ReadingBase = collections.namedtuple(
  '_ReadingBase', ['timestamp', 'value', 'comment', 'measure_method'])

class GlucoseReading(_ReadingBase):
  def __new__(cls, timestamp, value, meal=Meal.NONE, comment='',
              measure_method=MeasurementMethod.BLOOD_SAMPLE):
    """Constructor for the glucose reading object.

    Args:
      timestamp: (datetime) Timestamp of the reading as reported by the meter.
      value: (float) Value of the reading, in mg/dL.
      meal: (string) Meal-relativeness as reported by the reader, if any.
      comment: (string) Comment reported by the reader, if any.
      measure_method: (string) Measure method as reported by the reader if any,
        assuming blood sample otherwise.

    The value is stored in mg/dL, even though this is not the standard value,
    because at least most of the LifeScan devices report the raw data in this
    format.
    """
    instance = super(GlucoseReading, cls).__new__(
      cls, timestamp=timestamp, value=value, comment=comment,
      measure_method=measure_method)
    setattr(instance, 'meal', meal)
    return instance

  def get_value_as(self, to_unit):
    """Returns the reading value as the given unit.

    Args:
      to_unit: (Unit) The unit to return the value to.
    """
    return convert_glucose_unit(self.value, Unit.MG_DL, to_unit)

  def as_csv(self, unit):
    """Returns the reading as a formatted comma-separated value string."""
    return '"%s","%.2f","%s","%s","%s"' % (
      self.timestamp, self.get_value_as(unit), self.meal.value,
      self.measure_method.value, self.comment)

  def as_tsv(self, unit):
    """Returns the reading as a tab-separated value string.
        #1-Time	#2-Record Type	#3-Historic Glucose (mmol/L)-TYPE 0	#4-Scan Glucose (mmol/L)-TYPE 1	#5-Non-numeric Rapid-Acting Insulin	
        #6-Rapid-Acting Insulin (units)	#7-Non-numeric #8-Food	#9-Carbohydrates (grams)	#10-Non-numeric Long-Acting Insulin	
        #11-Long-Acting Insulin (units)	#12-Notes	#13-Strip Glucose (mmol/L)-TYPE 2	#14-Ketone (mmol/L)	#15-Meal Insulin (units)	
        #16-Correction Insulin (units)	#17-User Change Insulin (units)	#18-Previous Time	Updated Time\n
    """
    return "%s\t%s\t%s\t%s\t\t\t\t\t\t\t\t%s\t\t\t\t\t\t\t" % (
      '{:%Y/%m/%d %H:%M}'.format(self.timestamp),
      self._get_libre_type(),
      self._get_libre_historic_glucose(unit),
      self._get_libre_scan_glucose(unit),
      self._get_libre_strip_glucose(unit) )
      
  def _get_libre_type(self):
    """Returns the Libre file type code"""
    val = "-1"
    if self.measure_method == 'CGM':
      if self.comment.startswith ('(Sensor)'):
        val = "0"
      elif self.comment.startswith ('(Scan)'):
        val = "1"
    elif self.measure_method == 'blood sample':
      if self.comment.startswith ('(Blood)'):
        val = "2"
    return val

  def _get_libre_historic_glucose(self, unit):
    """returns Libre historic glucose - where Libre type = 0"""
    if self._get_libre_type() == "0":
      return str(round(self.get_value_as(unit),1))
    else:
      return ""

  def _get_libre_scan_glucose(self, unit):
    """returns Libre scan glucose - where Libre type = 1"""
    if self._get_libre_type() == "1":
      return str(round(self.get_value_as(unit),1))
    else:
      return ""

  def _get_libre_strip_glucose(self, unit):
    """returns Libre strip glucose - where Libre type = 2"""
    if self._get_libre_type() == "2":
      return str(round(self.get_value_as(unit),1))
    else:
      return ""

class KetoneReading(_ReadingBase):
  def __new__(cls, timestamp, value, comment='', **kwargs):
    """Constructor for the ketone reading object.

    Args:
      timestamp: (datetime) Timestamp of the reading as reported by the meter.
      value: (float) Value of the reading, in mmol/L.
      comment: (string) Comment reported by the reader, if any.

    The value is stored in mg/dL, even though this is not the standard value,
    because at least most of the LifeScan devices report the raw data in this
    format.
    """
    return super(KetoneReading, cls).__new__(
      cls, timestamp=timestamp, value=value, comment=comment,
      measure_method=MeasurementMethod.BLOOD_SAMPLE)

  def get_value_as(self, *args):
    """Returns the reading value in mmol/L."""
    return self.value

  def as_csv(self, unit):
    """Returns the reading as a formatted comma-separated value string."""
    return '"%s","%.2f","%s","%s"' % (
      self.timestamp, self.get_value_as(unit), self.measure_method.value,
      self.comment)

  def as_tsv(self, unit):
    """Returns the reading as a tab-separated value string.
        #1-Time	#2-Record Type	#3-Historic Glucose (mmol/L)-TYPE 0	#4-Scan Glucose (mmol/L)-TYPE 1	#5-Non-numeric Rapid-Acting Insulin	
        #6-Rapid-Acting Insulin (units)	#7-Non-numeric #8-Food	#9-Carbohydrates (grams)	#10-Non-numeric Long-Acting Insulin	
        #11-Long-Acting Insulin (units)	#12-Notes	#13-Strip Glucose (mmol/L)-TYPE 2	#14-Ketone (mmol/L)-TYPE 3	#15-Meal Insulin (units)	
        #16-Correction Insulin (units)	#17-User Change Insulin (units)	#18-Previous Time	Updated Time\n
    """
    return "%s\t%s\t\t\t\t\t\t\t\t\t\t\t%s\t\t\t\t\t\t" % (
      '{:%Y/%m/%d %H:%M}'.format(self.timestamp),
      "3",
      self.get_value_as(unit))

_MeterInfoBase = collections.namedtuple(
  '_MeterInfoBase', ['model', 'serial_number', 'version_info', 'native_unit'])

class MeterInfo(_MeterInfoBase):
  def __new__(cls, model, serial_number='N/A', version_info=(),
              native_unit=Unit.MG_DL):
    """Construct a meter information object.

    Args:
      model: (string) Human-readable model name, depending on driver.
      serial_number: (string) Optional serial number to identify the device.
      version_info: (list(string)) Optional hardware/software version information.
      native_unit: (Unit) Native unit of the device for display.
    """
    return super(MeterInfo, cls).__new__(
      cls, model=model, serial_number=serial_number, version_info=version_info,
      native_unit=native_unit)

  def __str__(self):
    version_information_string = 'N/A'
    if self.version_info:
      version_information_string = '\n    '.join(self.version_info).strip()

    return textwrap.dedent("""\
      {model}
      Serial Number: {serial_number}
      Version Information:
          {version_information_string}
      Native Unit: {native_unit}
      """).format(model=self.model, serial_number=self.serial_number,
                  version_information_string=version_information_string,
                  native_unit=self.native_unit.value)
