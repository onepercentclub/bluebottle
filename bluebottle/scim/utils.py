
import pyparsing as pp

from bluebottle.scim.scim_data.schemas import SCHEMAS


schemas = pp.one_of([schema['id'] for schema in SCHEMAS])
schema = (schemas + pp.Suppress(pp.Char(':'))).set_results_name('schema')

filter = (
    pp.Suppress('[') +
    pp.Word(pp.alphas) +
    pp.Suppress('eq') +
    pp.Suppress('"') +
    pp.Word(pp.alphas) +
    pp.Suppress('"]')
)

attr = pp.Word(pp.alphas).set_results_name('attrs', True)
filtered_attr = pp.Group(attr + filter).set_results_name('filters', True)

attrs = pp.delimitedList(filtered_attr | attr, '.')

scim_path = pp.Opt(schema) + attrs


class SCIMPath():
    def __init__(self, path):
        self.original = path
        self.parsed = scim_path.parse_string(self.original)

        # List of filters in the path e.g. `emails[type eq "bla"]`
        self.filters = self.parsed.filters.as_list() if self.parsed.filters else []
        # list of normal attrs in the path e.q. `emails`
        self.attrs = self.parsed.attrs.as_list() if self.parsed.attrs else []
        # the schema of the path: eg `urn:scim.....`
        self.schema = self.parsed.schema.as_list()[0] if self.parsed.schema else None

    def get(self, data):
        " Get path from data. Returns None if not set"
        for part in self.parsed:
            if not isinstance(part, str) and part.as_list() in self.filters:
                # Part is like `emails[type eq "work"]` which is parted to `["emails", "type", "work"]`
                # Try to get the correct item from the list
                attr = part.attrs[0]
                data = [item for item in data[attr] if item[part[1]] == part[2]][0]
            else:
                # Part is just a string
                try:
                    data = data[part]
                except KeyError:
                    return None

        return data

    def set(self, data, value):
        "Set path from data. Create the field if not set"
        for part in self.parsed[:-1]:
            if part in self.attrs or part == self.schema:
                # part is just a string or a schema. Just step in deeper
                if part not in data:
                    # If not set create it
                    data[part] = {}

                data = data[part]
            elif not isinstance(part, str) and part.as_list() in self.filters:
                # Part is like `emails[type eq "work"]` which is parted to `["emails", "type", "work"]`

                # First get `emails`
                attr = part.attrs[0]

                if attr not in data or not data[attr]:
                    # Not set, so create it
                    data[attr] = [{part[1]: part[2]}]
                elif not any(item for item in data if data.get(part[1]) == part[2]):
                    data[attr] = [{part[1]: part[2], **data[attr][0]}]

                # Return the correct item from the list
                data = [item for item in data[attr] if item[part[1]] == part[2]][0]

        # We have now traversed the complete list. Just set the value
        data[self.parsed[-1]] = value
