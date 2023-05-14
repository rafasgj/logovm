# This file is part of LogoVM
#
# Copyright (C) 2023 Rafael Guterres Jeffman
#
# This software is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <https://www.gnu.org/licenses/>.

"""LogoVM execptions."""


class ExtensionError(Exception):
    """General error for an extension."""


class LoaderError(Exception):
    """Errors for Loader or OS initialization."""


class InvalidLogoFile(LoaderError):
    """Exception raised when loading an invalid file."""


class InvalidOS(LoaderError):
    """Invalid OS loaded into LogoVM."""


class LogoVMOSError(Exception):
    """Generic error for a LogoVM OS."""


class LogoVMError(Exception):
    """Generic error for the LogoVM."""
