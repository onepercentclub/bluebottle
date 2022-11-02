
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

        self.filters = self.parsed.filters.as_list() if self.parsed.filters else []
        self.attrs = self.parsed.attrs.as_list() if self.parsed.attrs else []
        self.schema = self.parsed.schema.as_list()[0] if self.parsed.schema else None

    def get(self, data):
        for part in self.parsed:
            if not isinstance(part, str) and part.as_list() in self.filters:
                attr = part.attrs[0]
                data = [item for item in data[attr] if item[part[1]] == part[2]][0]
            else:
                try:
                    data = data[part]
                except KeyError:
                    return None

        return data

    def set(self, data, value):
        for part in self.parsed[:-1]:

            if part in self.attrs or part == self.schema:
                if part not in data:
                    data[part] = {}

                data = data[part]
            elif not isinstance(part, str) and part.as_list() in self.filters:
                attr = part.attrs[0]

                if attr not in data or not any(item for item in data if data.get(part[1]) == part[2]):
                    data[attr] = [{part[1]: part[2]}]

                data = [item for item in data[attr] if item[part[1]] == part[2]][0]

        data[self.parsed[-1]] = value
