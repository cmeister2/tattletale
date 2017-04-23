import sqlalchemy
import tattletale.database.models as tdmodels
import tattletale.database.version as tdversion
from tattletale.database.utility import get_or_create


class TestDatabase(object):
    def get_or_create_example_fqdn(self, log, database):
        fqdn, created = get_or_create(database.session, tdmodels.Fqdn, fqdn="www.example.com")
        log.debug("Return Fqdn %s (was created? %s)", fqdn, created)
        return fqdn

    def get_or_create_example_dnsa(self, log, database, fqdn):
        dnsa, created = get_or_create(database.session, tdmodels.DnsAResult, fqdn=fqdn)
        log.debug("Return DNS A %s (was created? %s)", dnsa, created)
        return dnsa

    def get_or_create_example_dnsc(self, log, database, fqdn):
        dnsc, created = get_or_create(database.session, tdmodels.DnsCnameResult, fqdn=fqdn)
        log.debug("Return DNS CNAME %s (was created? %s)", dnsc, created)
        return dnsc

    def get_or_create_example_ip_address(self, log, database):
        ip_address, created = get_or_create(database.session, tdmodels.IpAddress, ip_address="1.2.3.4")
        log.debug("Return IpAddress %s (was created? %s)", ip_address, created)
        return ip_address

    def get_or_create_example_portscan(self, log, database, ip_address):
        port_scan, created = get_or_create(database.session, tdmodels.PortScanResult, ip_address=ip_address)
        log.debug("Return Port Scan %s (was created? %s)", port_scan, created)
        return port_scan

    def get_or_create_example_portinfo(self, log, database, port_scan):
        port_info, created = get_or_create(database.session,
                                           tdmodels.PortInfo,
                                           port_scan=port_scan,
                                           port=80,
                                           info="http/apache")
        log.debug("Return Port Info %s (was created? %s)", port_info, created)
        return port_info

    def test_fqdn(self, log, database):
        # Create an FQDN.
        fqdn = self.get_or_create_example_fqdn(log, database)

        # Query the database for the inserted FQDN
        matches = database.session.query(tdmodels.Fqdn).filter_by(fqdn=fqdn.fqdn).all()
        log.info("Database matches for %s: %s", fqdn.fqdn, matches)
        assert (len(matches) == 1)

        # Try to insert the same FQDN again. It ought to fail because of the primary key.
        fqdn2 = tdmodels.Fqdn(fqdn=fqdn.fqdn)
        log.debug("Creating FQDN2: %s", fqdn2)
        database.session.add(fqdn2)
        try:
            database.session.commit()
        except sqlalchemy.exc.IntegrityError:
            log.info("Database insert failed as expected")
        finally:
            database.session.rollback()

        # The fqdn that we added won't have a DNS A result because that hasn't been created yet. Check that.
        fqdn = self.get_or_create_example_fqdn(log, database)
        log.debug("FQDN A result: %s", fqdn.a_result)
        assert (fqdn.a_result is None)

        # Delete the entry.
        database.session.delete(fqdn)

        fqdn_count = database.session.query(tdmodels.Fqdn).filter_by(fqdn=fqdn.fqdn).count()
        assert (fqdn_count == 0)
        log.debug("FQDNs are all deleted")

    def test_dns_a_result(self, log, database):
        # Create an FQDN.
        fqdn = self.get_or_create_example_fqdn(log, database)
        assert(fqdn.a_result is None)

        # Create a DNS A result
        dnsa = self.get_or_create_example_dnsa(log, database, fqdn)
        assert(fqdn.a_result == dnsa)

        # Query to ensure there's an entry in the database.
        query = database.session.query(tdmodels.DnsAResult).filter_by(fqdn=fqdn)
        matches = query.all()
        log.info("Database matches for %s: %s", fqdn, matches)
        assert (len(matches) == 1)

        # Delete the FQDN. This should delete the DNS A result due to cascading.
        database.session.delete(fqdn)
        assert (query.count() == 0)
        log.debug("DNS A results are all deleted")

    def test_ip_address(self, log, database):
        # Create an FQDN.
        fqdn = self.get_or_create_example_fqdn(log, database)

        # Create a DNS A result
        dnsa = self.get_or_create_example_dnsa(log, database, fqdn)

        # Create an IP address
        ip_address = self.get_or_create_example_ip_address(log, database)

        # Link the IP address to the DNS report.
        ip_address.a_results.append(dnsa)

        # Check that the DNS report now has a matching IP address
        assert (len(dnsa.addresses) == 1)
        assert (dnsa.addresses[0] == ip_address)

        # Delete the DNS A result. This shouldn't delete the IP address - other things might depend on that IP address.
        database.session.delete(dnsa)

        # Update IpAddress so it's up to date.
        database.session.refresh(ip_address)

        # Query to ensure there's an IpAddress entry in the database.
        assert (database.session.query(tdmodels.IpAddress).filter_by(ip_address=ip_address.ip_address).count() == 1)

        # Ensure the results for the IP address is now empty.  Theoretically this means the IP address is orphaned.
        assert (len(ip_address.a_results) == 0)

        # Cleanup
        database.session.delete(fqdn)
        database.session.delete(ip_address)

    def test_cnames(self, log, database):
        # Create an FQDN.
        fqdn = self.get_or_create_example_fqdn(log, database)

        # Create a DNS CNAME result.
        dnsc = self.get_or_create_example_dnsc(log, database, fqdn)

        # Create an FQDN that's the target of the DNS CNAME query.
        target_fqdn, _created = get_or_create(database.session, tdmodels.Fqdn, fqdn="target.example.com")

        # Link the DNS CNAME to the target FQDN
        target_fqdn.cnames.append(dnsc)
        log.debug("Session info: {session.dirty} {session.new}".format(session=database.session))

        # Check that the DNS CNAME has the right details
        database.session.commit()
        database.session.refresh(dnsc)

        assert (dnsc.target_fqdn == target_fqdn)

        # Delete the parent FQDN - this should remove the DNS CNAME entry
        database.session.delete(fqdn)
        dnsc_count = database.session.query(tdmodels.DnsCnameResult).filter_by(fqdn=fqdn).count()
        assert (dnsc_count == 0)

        # Delete the target FQDN
        database.session.delete(target_fqdn)

    def test_port_scan(self, log, database):
        # Create an IP address
        ip_address = self.get_or_create_example_ip_address(log, database)
        assert (ip_address.port_scan is None)

        # Create a Port Scan
        port_scan = self.get_or_create_example_portscan(log, database, ip_address)
        assert(ip_address.port_scan == port_scan)

        # Query to ensure there's an entry in the database.
        query = database.session.query(tdmodels.PortScanResult).filter_by(ip_address=ip_address)
        assert (query.count() == 1)

        # Delete the IpAddress. This should delete the port scan result due to cascading.
        database.session.delete(ip_address)

        assert (query.count() == 0)
        log.debug("Portscan results are all deleted")

    def test_portinfo(self, log, database):
        # Create an IP address
        ip_address = self.get_or_create_example_ip_address(log, database)
        assert (ip_address.port_scan is None)

        # Create a Port Scan
        port_scan = self.get_or_create_example_portscan(log, database, ip_address)
        assert(ip_address.port_scan == port_scan)

        # Create a PortInfo
        port_info = self.get_or_create_example_portinfo(log, database, port_scan)

        # Query to ensure there's an entry in the database.
        query = database.session.query(tdmodels.PortInfo).filter_by(port_scan=port_scan)
        assert (query.count() == 1)
        assert (len(port_scan.ports) == 1)
        assert (port_info in port_scan.ports)

        # Create another port
        port_info2, created = get_or_create(database.session,
                                            tdmodels.PortInfo,
                                            port_scan=port_scan,
                                            port=443,
                                            info="https/apache")
        database.session.refresh(port_scan)
        assert (query.count() == 2)
        assert (len(port_scan.ports) == 2)
        assert (port_info2 in port_scan.ports)

        # Delete the IpAddress. This should delete the port scan result and port info objects due to cascading.
        database.session.delete(ip_address)

        assert (query.count() == 0)
        log.debug("Port info results are all deleted")

    def test_version(self, log, database):
        # Get the current workspace version
        version = tdversion.get_version(database.engine, database.session)
        log.debug("Current workspace version: %d", version)