import bs4
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models.fields import TextField
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.safestring import mark_safe
from model_utils.models import TimeStampedModel

from rard.research.templatetags.entity_escape import entity_escape


class DynamicTextField(TextField):
    # class to search for dynamic links in text fields
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        if not self.null:
            field_name = self.name

            def update_editable_mentions(self, save=True):
                from rard.research.models import OriginalText

                # before editing we would like to check that
                # the text in aech of the mentions
                # is up to date
                value = getattr(self, field_name)
                soup = bs4.BeautifulSoup(value, features="html.parser")
                links = soup.find_all("span", class_="mention")

                for link in links:
                    print("got link %s" % link)
                    item_to_replace = link.find("span", contenteditable="false")
                    if not item_to_replace:
                        # format of the link is not as we expect so
                        # ignore it for now
                        continue

                    model_name = link.attrs.get("data-target", None)
                    pkstr = link.attrs.get("data-id", None)
                    char = link.attrs.get("data-denotation-char", None)

                    replacement = None

                    if model_name and pkstr and char:
                        try:
                            model = apps.get_model(
                                app_label="research", model_name=model_name
                            )
                            linked = model.objects.get(pk=int(pkstr))

                            if char == "@":
                                link_text = str(linked)
                            else:
                                # it's an apparatus criticus so we need
                                # show its index and any ordinal relating
                                # to the original text. e.g. if viewing this
                                # in a fragment's commentary we need to include
                                # any ordinal value

                                parent_pk = link.attrs.get("data-parent", None)
                                original_text_pk = link.attrs.get(
                                    "data-original-text", None
                                )
                                # if we are viewing the object in
                                # a parent's commentary
                                # then we need to potentially
                                # (if >1 original text) show its ordinal

                                link_text = ""

                                if parent_pk:
                                    original_text = OriginalText.objects.get(
                                        pk=int(original_text_pk)
                                    )
                                    link_text = (
                                        original_text.ordinal_with_respect_to_parent_object()  # noqa: E501
                                    )

                                # in any case show the app crit link index
                                link_text += str(linked.order + 1)

                            replacement = bs4.BeautifulSoup(
                                '<span contenteditable="false">'
                                '<span class="ql-mention-denotation-char">'
                                "{}</span>{}</span>".format(
                                    # char, linked.order + 1
                                    char,
                                    link_text,
                                ),
                                features="html.parser",
                            )
                            # we do need to replace the item as its index
                            # might have changed
                            item_to_replace.replace_with(replacement)

                        except (
                            AttributeError,
                            KeyError,
                            ValueError,
                            ObjectDoesNotExist,
                        ):
                            # the user has a bad link and needs to
                            # replace it, so mark it in error
                            link["class"].extend(["error"])

                setattr(self, field_name, str(soup))
                if save:
                    self.save_without_historical_record()

            def render_dynamic_content(self):
                # render the mentions as links or as app crit when viewing
                # the object on a web page
                from rard.research.models import OriginalText

                value = getattr(self, field_name)
                soup = bs4.BeautifulSoup(value, features="html.parser")
                links = soup.find_all("span", class_="mention")

                for link in links:
                    model_name = link.attrs.get("data-target", None)
                    pkstr = link.attrs.get("data-id", None)

                    replacement = None

                    if model_name and pkstr:
                        try:
                            model = apps.get_model(
                                app_label="research", model_name=model_name
                            )
                            linked = model.objects.get(pk=int(pkstr))
                            # is it something we can link to?
                            if getattr(linked, "get_absolute_url", False):
                                replacement = bs4.BeautifulSoup(
                                    '<a href="{}">{}</a>'.format(
                                        linked.get_absolute_url(), str(linked)
                                    ),
                                    features="html.parser",
                                )
                            else:
                                # else currently that means it's an
                                # apparatus criticus item
                                parent_pk = link.attrs.get("data-parent", None)
                                original_text_pk = link.attrs.get(
                                    "data-original-text", None
                                )
                                # if we are viewing the object in a parent's
                                # commentary then we need to potentially
                                # (if >1 original text) show its ordinal

                                display_str = ""

                                if parent_pk:
                                    original_text = OriginalText.objects.get(
                                        pk=int(original_text_pk)
                                    )
                                    display_str = (
                                        original_text.ordinal_with_respect_to_parent_object()  # noqa: E501
                                    )  # noqa

                                # in any case show the app crit link index
                                display_str += str(linked.order + 1)

                                replacement = bs4.BeautifulSoup(
                                    '<sup id="{}" data-toggle="tooltip" '
                                    'data-html="true" '
                                    'data-placement="top" '
                                    'style="cursor:pointer;color:blue" '
                                    "title=\"<span class='historical'>{}"
                                    '</span>">'
                                    "{}</sup>".format(
                                        linked.get_anchor_id(),
                                        mark_safe(entity_escape(linked.content)),
                                        display_str,
                                    ),
                                    features="html.parser",
                                )

                        except (
                            AttributeError,
                            KeyError,
                            ValueError,
                            ObjectDoesNotExist,
                        ):
                            # indicate a bad link. Alternative we could use
                            # the content of the definition as a fall-back
                            # and render that? If so, just remove the
                            # replacement line below and that will happen
                            # i.e. <dynamic>this content here</dynamic>

                            # try and extract the name not the @ from
                            # the content
                            # but fallback to the full link text if need be
                            linktext = str(link.text)
                            linktext = linktext.replace("@", "")

                            replacement = bs4.BeautifulSoup(
                                '<span class="bad-link">{}</span>'.format(linktext),
                                features="html.parser",
                            )

                        # replace with the new link in the rendered output
                        if replacement:
                            link.replace_with(replacement)

                return str(soup)

            def link_bibliography_mentions(self):
                """
                If this model has a related antiquarian, search content
                for @mentions referencing bibliographyitems and add them
                to antiquarian.bibliography_items.
                If there is a related (anonymous)fragment or testimonium,
                do the same for any related antiquarians
                """
                if self.fragment:
                    antiquarians = [
                        link.antiquarian
                        for link in self.fragment.get_all_links()
                        if link.antiquarian is not None
                    ]

                if self.anonymousfragment:
                    antiquarians = [
                        link.antiquarian
                        for link in self.anonymousfragment.get_all_links()
                        if link.antiquarian is not None
                    ]

                if self.testimonium:
                    antiquarians = [
                        link.antiquarian
                        for link in self.testimonium.get_all_links()
                        if link.antiquarian is not None
                    ]

                if self.antiquarian:
                    antiquarians = [self.antiquarian]

                value = getattr(self, field_name)
                soup = bs4.BeautifulSoup(value, features="html.parser")
                links = soup.find_all("span", class_="mention")

                for link in links:
                    model_name = link.attrs.get("data-target", None)
                    pkstr = link.attrs.get("data-id", None)
                    if model_name == "bibliographyitem" and pkstr:
                        try:
                            model = apps.get_model(
                                app_label="research", model_name=model_name
                            )
                            bib_item = model.objects.get(pk=int(pkstr))
                            for ant in antiquarians:
                                ant.bibliography_items.add(bib_item)

                        except ObjectDoesNotExist:
                            # If bibliography item has been deleted, we want to ignore,
                            # as it should still be rendered as unlinked
                            pass

            # here we add a method to the class. So if the dynamic field of
            # our class is called 'content' then the method will be
            # 'render_content' etc
            setattr(cls, "render_%s" % self.name, render_dynamic_content)
            setattr(cls, "update_%s_mentions" % self.name, update_editable_mentions)
            setattr(
                cls,
                f"link_bibliography_mentions_in_{self.name}",
                link_bibliography_mentions,
            )


class ObjectLock(models.Model):
    class Meta:
        app_label = "research"

    locked_at = models.DateTimeField(null=True, editable=False)
    locked_by = models.ForeignKey(
        "users.User", null=True, editable=False, on_delete=models.SET_NULL
    )

    # optional end datetime for the lock
    locked_until = models.DateTimeField(null=True, default=None)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()

    content_object = GenericForeignKey()


class ObjectLockRequest(TimeStampedModel, models.Model):
    class Meta:
        app_label = "research"

    # a request to break the lock. All deleted when the lock is deleted
    object_lock = models.ForeignKey(ObjectLock, on_delete=models.CASCADE)

    from_user = models.ForeignKey("users.User", on_delete=models.CASCADE)


class BaseModel(TimeStampedModel, models.Model):
    # defines a base model with any required
    # additional common functionality
    class Meta:
        abstract = True


class LockableModel(models.Model):
    class Meta:
        abstract = True

    object_locks = GenericRelation(ObjectLock)

    def get_object_lock(self):
        return self.object_locks.first()

    def lock(self, user, lock_until=None):
        ObjectLock.objects.create(
            locked_at=timezone.now(),
            locked_by=user,
            content_object=self,
            locked_until=lock_until,
        )

    def break_lock(self, broken_by_user):
        if not broken_by_user.can_break_locks:
            return

        # someone with permission to do so has broken the lock
        object_lock = self.get_object_lock()

        # prepare email to lock owner
        html_email_template = "research/emails/item_lock_broken.html"
        current_site = get_current_site(None)
        context = {
            "user": object_lock.locked_by,
            "broken_by_user": broken_by_user,
            "lock": object_lock,
            "site_name": current_site.name,
            "domain": current_site.domain,
        }
        content = render_to_string(html_email_template, context)
        email_data = [
            (
                "The item you were editing has been made available",
                "",
                settings.DEFAULT_FROM_EMAIL,
                [object_lock.locked_by.email],
            ),
            {"html_message": content, "fail_silently": False},
        ]

        # break lock
        self.unlock()

        # send email to lock owner
        send_mail(*email_data[0], **email_data[1])

    def send_long_lock_email(self):
        # where a user has had a lock for a long time, we send them
        # an email to tell them to hurry or ask if they still need it
        object_lock = self.get_object_lock()

        # prepare email to lock owner
        html_email_template = "research/emails/long_lock_warning.html"
        current_site = get_current_site(None)
        context = {
            "user": object_lock.locked_by,
            "lock": object_lock,
            "site_name": current_site.name,
            "domain": current_site.domain,
        }
        content = render_to_string(html_email_template, context)

        send_mail(
            "You have had an item locked for a while",
            "",
            settings.DEFAULT_FROM_EMAIL,
            [object_lock.locked_by.email],
            html_message=content,
            fail_silently=False,
        )

    def unlock(self):
        object_lock = self.get_object_lock()

        if not object_lock:
            return

        # collect data emails using info before we delete it
        # and if deletion works okay then send the mails after
        # (we don't have access to the info once we delete it)
        email_data_list = []

        # notify anyone with a lock request of the event
        for lock_request in object_lock.objectlockrequest_set.all():
            html_email_template = "research/emails/item_unlocked.html"
            current_site = get_current_site(None)
            context = {
                "user": object_lock.locked_by,
                "from_user": lock_request.from_user,
                "lock": object_lock,
                "site_name": current_site.name,
                "domain": current_site.domain,
            }
            content = render_to_string(html_email_template, context)
            email_data = [
                (
                    "The item you requested has become available",
                    "",
                    settings.DEFAULT_FROM_EMAIL,
                    [lock_request.from_user.email],
                ),
                {"html_message": content, "fail_silently": False},
            ]
            email_data_list.append(email_data)

        # delete any lock records
        self.object_locks.all().delete()

        # send the mails we prepared
        for args, kwargs in email_data_list:
            send_mail(*args, **kwargs)

    def check_lock_expired(self):
        object_lock = self.get_object_lock()
        if not object_lock:
            return

        if object_lock.locked_until and object_lock.locked_until < timezone.now():
            # unlock silently
            # self.object_locks.all().delete()

            # or unlock noisily (sends emails)
            self.unlock()

    def is_locked(self):
        # until cron job sorted, inspect expired locks in a lazy manner
        self.check_lock_expired()
        return self.object_locks.exists()

    @property
    def locked_by(self):
        try:
            return self.get_object_lock().locked_by
        except AttributeError:
            return None

    @property
    def locked_until(self):
        try:
            return self.get_object_lock().locked_until
        except AttributeError:
            return None

    @property
    def locked_at(self):
        try:
            return self.get_object_lock().locked_at
        except AttributeError:
            return None

    def request_lock(self, from_user):
        self.get_object_lock().objectlockrequest_set.create(from_user=from_user)
        object_lock = self.get_object_lock()

        # notify lock owner of the request
        html_email_template = "research/emails/request_lock.html"
        current_site = get_current_site(None)
        context = {
            "user": object_lock.locked_by,
            "from_user": from_user,
            "lock": object_lock,
            "site_name": current_site.name,
            "domain": current_site.domain,
        }
        content = render_to_string(html_email_template, context)
        send_mail(
            "Request to edit record",
            "",
            settings.DEFAULT_FROM_EMAIL,
            [self.get_object_lock().locked_by.email],
            html_message=content,
            fail_silently=False,
        )


class DatedModel(models.Model):
    # for models that have a date range or value, such as
    # antiquarians, works, books, citing authors etc

    class Meta:
        abstract = True

    # Store as integer. Negative means BC, positive is AD
    order_year = models.IntegerField(
        default=None,
        null=True,
        blank=True,
        help_text="Enter a negative integer value for BC, positive for AD",
    )

    date_range = models.CharField(max_length=256, default="", blank=True)

    def display_date_range(self):
        return self.date_range


class OrderableModel(models.Model):
    class Meta:
        ordering = ["order"]
        abstract = True

    order = models.PositiveIntegerField(default=None, null=True, blank=True)

    order_index_start = 0

    def related_queryset(self):
        # by default sort according to all objects of this class
        # and this can be overidden in the subclasses in case
        # you need to order e.g. wrt a particular data member e.g. work
        return self.__class__.objects.all()

    def prev(self):
        return self.related_queryset().filter(order__lt=self.order).last()

    def next(self):
        return self.related_queryset().filter(order__gt=self.order).first()

    def swap(self, replacement):
        self.order, replacement.order = replacement.order, self.order
        self.save()
        replacement.save()

    def move_to(self, pos):
        # move to a particular index in the set
        old_pos = self.order
        if pos == old_pos:
            return

        # if beyond the end do nothing (UI bug)
        if pos >= self.related_queryset().count() + self.order_index_start:
            return

        if pos < old_pos:
            to_reorder = (
                self.related_queryset().exclude(pk=self.pk).filter(order__gte=pos)
            )
            reindex_start_pos = pos + 1
        else:
            to_reorder = (
                self.related_queryset().exclude(pk=self.pk).filter(order__lte=pos)
            )
            reindex_start_pos = self.order_index_start

        with transaction.atomic():
            for count, obj in enumerate(to_reorder):
                obj.order = count + reindex_start_pos
                obj.save()

            self.order = pos
            self.save()

    def up(self):
        previous = self.prev()
        if previous:
            self.swap(previous)

    def down(self):
        next_ = self.next()
        if next_:
            self.swap(next_)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.order = self.related_queryset().count()
        super().save(*args, **kwargs)
