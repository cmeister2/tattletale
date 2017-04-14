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
        log.debug("Return Fqdn %s Created? %s", fqdn, created)
        return fqdn

    def get_or_create_example_dnsa(self, log, database, fqdn):
        dnsa, created = self.get_or_create(log, database, tdmodels.DnsAResult, fqdn=fqdn)
        log.debug("Return DNS A %s Created? %s", dnsa, created)
        return dnsa

    def test_fqdn(self, log, database):
        # Create an FQDN.
        fqdn = self.get_or_create_example_fqdn(log, database)

        # Query the database for the inserted FQDN
        matches = database.session.query(tdmodels.Fqdn).filter_by(fqdn=fqdn.fqdn).all()
        log.info("Database matches for %s: %s", fqdn.fqdn, matches)
        assert(len(matches) == 1)

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
        fqdn = matches[0]
        log.debug("FQDN A result: %s", fqdn.a_result)
        assert(fqdn.a_result is None)

        # Delete the entry.
        database.session.delete(fqdn)

        fqdn_count = database.session.query(tdmodels.Fqdn).filter_by(fqdn=fqdn.fqdn).count()
        assert(fqdn_count == 0)
        log.debug("FQDNs are all deleted")

    def test_dns_a_result(self, log, database):
        # Create an FQDN.
        fqdn = self.get_or_create_example_fqdn(log, database)

        # Create a DNS A result
        dnsa = self.get_or_create_example_dnsa(log, database, fqdn)

        # Query to ensure there's an entry in the database.
        matches = database.session.query(tdmodels.DnsAResult).filter_by(fqdn=fqdn).all()
        log.info("Database matches for %s: %s", fqdn, matches)
        assert(len(matches) == 1)

        # Delete the FQDN. This should delete the DNS A result due to cascading.
        database.session.delete(fqdn)

        dnsa_count = database.session.query(tdmodels.DnsAResult).filter_by(fqdn=fqdn).count()
        assert(dnsa_count == 0)
        log.debug("DNS A results are all deleted")