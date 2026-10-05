from encodings.utf_8 import encode
import hashlib
import hmac
import json
from ast import Bytes
from hmac import HMAC

class Crypto:
  @staticmethod
  def compute_sha256_hash(message: str, secret: str) -> str:

    # whitespaces that were created during json parsing process must be removed
    hash = hmac.new(secret.encode(), message.encode() ,digestmod=hashlib.sha256)
    return hash.hexdigest()

  @staticmethod
  def calculate_hmac(self, secret: str, headerParams: dict, body: str='') -> str:

    data = []
    for key,value in headerParams.items():
      if key.startswith('checkout-'):
        data.append('{key}:{value}'.format(key = key, value = value))

    data.append(body)
    return self.compute_sha256_hash('\n'.join(data), secret)
  

class Item:
  def __init__(self, unitPrice: int, units: int, vatPercentage: int, productCode: str, deliveryDate: str) -> None:
    self.unitPrice = unitPrice
    self.units = units
    self.vatPercentage = vatPercentage
    self.productCode = productCode
    self.deliveryDate = deliveryDate


class Customer:
  def __init__(self, email: str, firstName: str, lastName: str, phone: str, vatId: str, companyName: str) -> None:
    self.email = email
    self.firstName = firstName
    self.lastName = lastName
    self.phone = phone
    self.vatId = vatId
    self.companyName = companyName


class DeliveryAddress:
  def __init__(self, streetAddress: str, postalCode: str, city: str, country: str) -> None:
    self.streetAddress = streetAddress
    self.postalCode = postalCode
    self.city = city
    self.country = country


class RedirectUrls:
  def __init__(self, success: str, cancel: str) -> None:
    self.success = success
    self.cancel = cancel


class Body:
  def __init__(self, stamp: str, reference: str, amount: int,
    currency: str, language: str, customer: Customer, deliveryAddress: DeliveryAddress, redirectUrls: RedirectUrls) -> None:
    self.stamp = stamp
    self.reference = reference
    self.amount = amount
    self.currency = currency
    self.language = language
    self.customer = customer
    self.deliveryAddress = deliveryAddress
    self.redirectUrls = redirectUrls

  # create toDictionary() method to customize a converter of object class to dict type
  def toDictionary(self) -> dict:
    return dict({
      "stamp":self.stamp,
      "reference":self.reference,
      "amount":self.amount,
      "currency":self.currency,
      "language":self.language,
      "customer":self.customer.__dict__,
      "deliveryAddress":self.deliveryAddress.__dict__,
      "redirectUrls":self.redirectUrls.__dict__
    })


