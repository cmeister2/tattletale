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

    # FQDNs are the linked one-to-one parent of DNS A results, if an A scan has been performed.
    a_result = relationship("DnsAResult",
                            back_populates="fqdn",
                            uselist=False,
                            cascade="all,delete-orphan")

    def __repr__(self):
        return "{self.__class__.__name__}(id={self.id}, fqdn='{self.fqdn}')".format(self=self)


dns_ip_assoc = Table('dns_ip_assoc', Base.metadata,
    Column('dns_id', Integer, ForeignKey('dnsaresults.id')),
    Column('ipaddress_id', Integer, ForeignKey('ipaddress.id'))
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
    __tablename__ = "ipaddress"
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(100), unique=True)

    # Linked to potentially many DNS results
    a_results = relationship("DnsAResult",
                             secondary=dns_ip_assoc,
                             back_populates="addresses")
