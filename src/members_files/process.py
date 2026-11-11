"""Compare BBO membership files."""

from dataclasses import dataclass

from members_files.csv_utils import get_dict_from_csv_file


@dataclass
class Member:
    """Represents a member."""

    ebu: str
    first_name: str
    last_name: str
    bbo: str
    status: str


class Compare:
    def __init__(self, paths: dict[str, str]) -> None:
        self.paths = paths
        self.missing_from_include = {}
        self.missing_from_bbo = {}
        self.members_ebu = {}  # dict of members from members' database
        self.members_bbo = {}  # fist of members from bb_names file
        self.duplicates = {}
        self.bbo_names = []
        self.duplicates_in_bbo = []

    def compare(self) -> None:
        (members, members_fields) = get_dict_from_csv_file(
            self.paths["Membership"], "EBU"
        )
        del members_fields
        for item in members.values():
            if item["EBU"] == "EBU":
                continue
            member = Member(
                str(int(item["EBU"])),
                item["FIRSTNAME"],
                item["SURNAME"],
                item["BBOUSERNAME"].lower(),
                item["STATUS"],
            )

            self.members_ebu[member.ebu] = member

        include_list = self._get_include_list(self.paths["BBO include"])

        self.members_bbo = self._get_bbo_names(self.paths["BBO names"])

        # Select all members with a BBO username that are not
        # in the include_list or bbo_names file
        for ebu, member in self.members_ebu.items():
            if member.bbo and member.status == "Member":
                if member.bbo not in include_list:
                    self.missing_from_include[ebu] = self.members_ebu[ebu]
                if member.ebu not in self.members_bbo:
                    self.missing_from_bbo[ebu] = self.members_ebu[ebu]

        if self.duplicates_in_bbo:
            for member in sorted(
                self.duplicates_in_bbo, key=lambda x: x.last_name
            ):
                self.duplicates[member.ebu] = member

    def _get_include_list(self, path: str) -> list:
        with open(path, encoding="utf8") as f_include:
            data = f_include.read().split("\n")
            return [name.lower() for name in data]

    def _get_bbo_names(self, path: str) -> dict:
        output = {}
        with open(path, encoding="utf8") as f_names:
            bbo_names = f_names.read().strip("\n").split("\n")

        for item in bbo_names:
            record = item.split(",")
            record = [field.strip() for field in record]
            member = Member(
                str(int(record[3])),
                record[1],
                record[2],
                record[0].lower(),
                "",
            )
            if member.ebu in output:
                self.duplicates_in_bbo.append(member)
                # dup_member = output[member.ebu]
                # self.duplicates_in_bbo.append(dup_member)

            output[member.ebu] = member
        return output

    def create_include_from_members(self) -> None:
        include_bbo = []

        # some members don't have a BBO username on BridgeWebs db,
        # so we need to check both dictionaries
        for member in {**self.members_bbo, **self.members_ebu}.values():
            if member.ebu in self.members_ebu:
                status = self.members_ebu[member.ebu].status

            if member.bbo and status == "Member":
                include_bbo.append(member.bbo)

        path = self.paths["BBO include"]
        with open(path, "w", encoding="utf8") as f_include:
            f_include.write("\n".join(sorted(include_bbo)))
