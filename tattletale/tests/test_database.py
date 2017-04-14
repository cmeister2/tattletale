import tattletale.database.models as tdmodels
import sqlalchemy


class TestDatabase(object):
    def get_or_create(self, log, database, model, defaults=None, **kwargs):
        instance = database.session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance, False
        else:
            params = dict(
                (k, v) for k, v in kwargs.items() if not isinstance(v, sqlalchemy.sql.expression.ClauseElement))
            params.update(defaults or {})
            instance = model(**params)
            database.session.add(instance)
            database.session.commit()
            return instance, True

    def get_or_create_example_fqdn(self, log, database):
        fqdn, created = self.get_or_create(log, database, tdmodels.Fqdn, fqdn="www.example.com")
        log.debug("Return Fqdn %s (was created? %s)", fqdn, created)
        return fqdn

    def get_or_create_example_dnsa(self, log, database, fqdn):
        dnsa, created = self.get_or_create(log, database, tdmodels.DnsAResult, fqdn=fqdn)
        log.debug("Return DNS A %s (was created? %s)", dnsa, created)
        return dnsa

    def get_or_create_example_dnsc(self, log, database, fqdn):
        dnsc, created = self.get_or_create(log, database, tdmodels.DnsCnameResult, fqdn=fqdn)
        log.debug("Return DNS CNAME %s (was created? %s)", dnsc, created)
        return dnsc

    def get_or_create_example_ip_address(self, log, database, dnsa):
        ip_address, created = self.get_or_create(log, database, tdmodels.IpAddress, ip_address="1.2.3.4")
        log.debug("Return IpAddress %s (was created? %s)", ip_address, created)
        return ip_address

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

        # Create a DNS A result
        dnsa = self.get_or_create_example_dnsa(log, database, fqdn)

        # Query to ensure there's an entry in the database.
        matches = database.session.query(tdmodels.DnsAResult).filter_by(fqdn=fqdn).all()
        log.info("Database matches for %s: %s", fqdn, matches)
        assert (len(matches) == 1)

        # Delete the FQDN. This should delete the DNS A result due to cascading.
        database.session.delete(fqdn)

        dnsa_count = database.session.query(tdmodels.DnsAResult).filter_by(fqdn=fqdn).count()
        assert (dnsa_count == 0)
        log.debug("DNS A results are all deleted")

    def test_ip_address(self, log, database):
        # Create an FQDN.
        fqdn = self.get_or_create_example_fqdn(log, database)

        # Create a DNS A result
        dnsa = self.get_or_create_example_dnsa(log, database, fqdn)

        # Create an IP address
        ip_address = self.get_or_create_example_ip_address(log, database, dnsa)

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
        target_fqdn, _created = self.get_or_create(log, database, tdmodels.Fqdn, fqdn="target.example.com")

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
