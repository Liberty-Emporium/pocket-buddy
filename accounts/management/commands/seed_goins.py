"""Idempotent bootstrap for customer #1: Jason Goins, Attorney at Law."""

import os

from django.core.management.base import BaseCommand

from accounts.models import Organization, User


class Command(BaseCommand):
    help = "Create the Goins organization plus a boss and secretary user."

    def handle(self, *args, **options):
        org, created = Organization.objects.get_or_create(
            slug="goins-law",
            defaults={
                "name": "Jason Goins, Attorney at Law",
                "display_name": "Jason Goins, Attorney at Law",
            },
        )
        self.stdout.write(
            ("Created" if created else "Found") + f" organization: {org.name}"
        )

        # Passwords come from env so we never hardcode a secret in the repo.
        boss_pw = os.environ.get("BOSS_PASSWORD", "changeme-boss")
        sec_pw = os.environ.get("SECRETARY_PASSWORD", "changeme-secretary")

        for username, role, pw in [
            ("jason", User.Role.BOSS, boss_pw),
            ("secretary", User.Role.SECRETARY, sec_pw),
        ]:
            user, u_created = User.objects.get_or_create(
                username=username,
                defaults={"organization": org, "role": role},
            )
            # Keep org/role correct even on re-run; only set password on create.
            user.organization = org
            user.role = role
            if u_created:
                user.set_password(pw)
            user.save()
            self.stdout.write(
                ("Created" if u_created else "Updated")
                + f" user: {username} ({role})"
            )

        self.stdout.write(self.style.SUCCESS("Seed complete."))
