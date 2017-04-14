from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Fqdn(Base):
    """
    A fully qualified domain name.
    """
    __tablename__ = "fqdns"
    id = Column(Integer, primary_key=True)
    fqdn = Column(String(255), unique=True)

    # FQDNs are the parents of DNS scans
    a_result = relationship("DnsAResult", back_populates="fqdn", uselist=False, cascade="all,delete-orphan")
    cname_result = relationship("DnsCnameResult", back_populates="fqdn", uselist=False, cascade="all,delete-orphan")

    # FQDNs may be the result of a CName query - if so, this will point to the queries that pointed at this FQDN.
    cnames = relationship("DnsCnameResult", back_populates="target_fqdn")

    def __repr__(self):
        return "{self.__class__.__name__}(id={self.id}, fqdn='{self.fqdn}')".format(self=self)


dns_ip_assoc = Table('dns_ip_assoc', Base.metadata,
    Column('dns_id', Integer, ForeignKey('dnsaresults.id')),
    Column('ipaddress_id', Integer, ForeignKey('ipaddresses.id'))
)


class DnsAResult(Base):
    """
    Results from doing a DNS A query on an FQDN.
    """
    __tablename__ = "dnsaresults"
    id = Column(Integer, primary_key=True)
    fqdn_id = Column(Integer, ForeignKey("fqdns.id"), unique=True)

    # Linked to a parent FQDN.
    fqdn = relationship("Fqdn", back_populates="a_result")

    # Linked to potentially many IP addresses
    addresses = relationship("IpAddress",
                             secondary=dns_ip_assoc,
                             back_populates="a_results")


class IpAddress(Base):
    """
    IP address retrieved from a DNS query
    """
    __tablename__ = "ipaddresses"
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(100), unique=True)

    # Linked to potentially many DNS results
    a_results = relationship("DnsAResult",
                             secondary=dns_ip_assoc,
                             back_populates="addresses")

    # May link to a port scan result
    port_scan = relationship("PortScanResult", back_populates="ip_address", uselist=False, cascade="all,delete-orphan")

cname_fqdn_assoc = Table('cname_fqdn_assoc', Base.metadata,
    Column('cname_id', Integer, ForeignKey('dnscnameresults.id'), unique=True),
    Column('fqdn_id', Integer, ForeignKey('fqdns.id'))
)


class DnsCnameResult(Base):
    """
    Results from doing a DNS CNAME query on an FQDN.
    """
    __tablename__ = "dnscnameresults"
    id = Column(Integer, primary_key=True)
    fqdn_id = Column(Integer, ForeignKey("fqdns.id"), unique=True)

    # Linked to a parent FQDN.
    fqdn = relationship("Fqdn", back_populates="cname_result")

    # Potentially linked to a child FQDN
    target_fqdn = relationship("Fqdn",
                               secondary=cname_fqdn_assoc,
                               back_populates="cnames",
                               uselist=False)


class PortScanResult(Base):
    """
    Results from doing a port scan on an IP address
    """
    __tablename__ = "portscanresults"
    id = Column(Integer, primary_key=True)
    ip_address_id = Column(Integer, ForeignKey("ipaddresses.id"), unique=True)

    # Linked to a parent IP address.
    ip_address = relationship("IpAddress", back_populates="port_scan")

    # # Linked to potentially many Port results
