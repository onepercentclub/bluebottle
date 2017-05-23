import copy
import json
import logging
from collections import OrderedDict


class DictFormatter(logging.Formatter):
    """Used for formatting log records into a dict."""
    default_regular_attrs = ["name", "message", "levelname", "module", "asctime"]
    ignore_builtin_attrs = ["levelno", "pathname", "filename", "lineno", "funcName", "created", "msecs",
                            "relativeCreated", "thread", "threadName", "process", "processName", "args", "msg",
                            "exc_info", "exc_text", "stack_info"]

    def __init__(self, *args, **kwargs):
        """
        :param list regular_attrs: A list of strings specifying built-in python
            logging args that should be included in each output dict.
            If not specified, all args will be used.  Setting to an empty list
            will disable regular args.
        :param list extra_attrs: A list of strings specifying additional
            arguments that may exist on the log record instances and
            should be included in the messages.  By default this will
            be calculated for you to include all available extra attributes.
        :param bool preserve_order: If ``True``, will cause format() to
            return an OrderedDict with the keys in the same order every time.
            Default: ``False``.
        :param list specific_order:  If set to a list and preserve_order is
            ``True``, will cause the keys to be in this order if they exist.
            Keys to be included that are not listed here will be included after
            the ones which are specified.  Default is ``None``, which will cause
            the default_regular_attrs to appear first in the order they are
            in the class attribute, and then extra attributes to be included
            in alphabetical order.

        Note:
            The attribute useful_attrs is deprecated and maintained for backward compatibility.
            You should stop using it.
        """
        regular_attrs = kwargs.pop('regular_attrs', None)
        extra_attrs = kwargs.pop('extra_attrs', None)
        preserve_order = kwargs.pop('preserve_order', False)
        specific_order = kwargs.pop('specific_order', None)
        super(DictFormatter, self).__init__(*args, **kwargs)
        if regular_attrs is None:
            self.regular_attrs = copy.deepcopy(self.default_regular_attrs)
        else:
            self.regular_attrs = regular_attrs
        self.extra_attrs = extra_attrs

        self.useful_attrs = self.regular_attrs
        if extra_attrs is not None:
            self.useful_attrs += extra_attrs

        self.preserve_order = preserve_order
        self.specific_order = specific_order

        self.all_builtin_attrs = set(self.default_regular_attrs + self.ignore_builtin_attrs)

    def format(self, record):
        """
        Formats a log record into a dictionary using the arguments given to __init__.
        """
        message = super(DictFormatter, self).format(record)
        record_dict = record.__dict__
        record_dict["message"] = message
        if "asctime" not in record_dict:
            record_dict["asctime"] = self.formatTime(record)

        if self.extra_attrs is not None:
            extra_attrs = self.extra_attrs
        else:
            extra_attrs = list(set(record_dict.keys()) - self.all_builtin_attrs)
        useful_attrs = self.regular_attrs + extra_attrs

        if not self.preserve_order:
            msg_dict = {}
            for attr_name in useful_attrs:
                if attr_name in record_dict:
                    msg_dict[attr_name] = record_dict[attr_name]
            return msg_dict
        else:
            useful_attrs_set = set(useful_attrs)
            if self.specific_order is not None:
                specific_order = self.specific_order
                unordered_keys = useful_attrs_set - set(specific_order)
                if unordered_keys:
                    specific_order += sorted(list(unordered_keys), key=str.lower)
            else:
                specific_order = self.regular_attrs + sorted(extra_attrs, key=str.lower)

            msg_proplist = []
            for attr_name in specific_order:
                if attr_name in record_dict:
                    msg_proplist.append((attr_name, record_dict[attr_name]))
            return OrderedDict(msg_proplist)


class JsonFormatter(DictFormatter):
    def formatException(self, exc_info):
        """
        Format an exception so that it prints on a single line.
        """

        result = super(JsonFormatter, self).formatException(exc_info)
        return repr(result)  # or format into one line however you want to

    def format(self, record):
        s = super(JsonFormatter, self).format(record)
        return json.dumps(s)
