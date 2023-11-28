"""
This script contains the Domenico Robbins solutions.

For detailed algorithms, please see Gutierrez-Neri et al., 2009. Analytical modelling of fringe and core
biodegradation in groundwater plumes. Journal of Contaminant Hydrology, 107, 1-9. doi:10.1016/j.jconhyd.2009.02.007.

@author: Wei Mao <wm23a@fsu.edu>
"""
import math
import numpy as np


vertorized_erf = np.vectorize(math.erf)
vertorized_erfc = np.vectorize(math.erfc)


class DomenicoRobbins:
    """Non-reactive solute transport in 3D
    based on equation 1, 2, and 3 in Gutierrez-Neri et al., 2009
    """
    def __init__(self, name, concinit, dx, dy, dz, Y, Z, k, v, t):
        """
        concinit, concentration at t=0
        dx, dy, dz, dispersivity in x, y, z direction
        Y, Z, length of the domain in y, z direction
        v, average velocity
        t, time
        """
        self.name = name
        self.concinit = concinit
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.Y = Y
        self.Z = Z
        self.k = k
        self.v = v
        self.t = t

        if self.name == "DomenicoRobbins":
            self.k = 0
        elif self.name == "DomenicoRobbins2D":
            self.k = 0
            self.dz = 0
            self.Z = 0
        elif self.name == "DomenicoRobbinsSS":
            self.k = 0
            self.t = -1
        elif self.name == "DomenicoRobbinsSS2D":
            self.k = 0
            self.dz = 0
            self.Z = 0
            self.t = -1
        elif self.name == "DomenicoRobbinsSSDecay2D":
            self.dz = 0
            self.Z = 0
            self.t = -1
            if self.k <= 0:
                raise ValueError("Decay constant must be greater than 0")
            self.decay_sqrt = math.sqrt(1 + (4 * self.k * self.dx / self.v))
        elif self.name == "DomenicoRobbins2DModified":
            self.dz = 0
            self.Z = 0
            self.k = 0
            self.t = -1
        elif self.name == "DomenicoRobbins2DModified_VD":
            pass
        else:
            raise ValueError("Invalid model name")

        self.s = concinit / 8
        if t >= 0:
            self.vt = v * t
            self.xden = 2 * math.sqrt(dx * v * t)
        else:
            self.vt = 0
            self.xden = 0
        self.yover2 = Y / 2
        self.zover2 = Z  # without the /2

    def eval(self, x, y, z):
        try:
            nx = len(x)
            ny = len(y)
            x = np.tile(x, ny).reshape(ny, nx)
            y = np.tile(y, nx).reshape(nx, ny).transpose()
        except TypeError:
            if isinstance(x, int) or isinstance(x, float):
                pass
            else:
                raise TypeError("x must be a number or a numpy array")
        if self.name == "DomenicoRobbins":
            yden = 2 * np.sqrt(self.dy * x)
            zden = 2 * np.sqrt(self.dz * x)
            erfy_p1 = (y + self.yover2) / yden
            erfy_p2 = (y - self.yover2) / yden
            erfz_p1 = (z + self.zover2) / zden
            erfz_p2 = (z - self.zover2) / zden

            erfy_p1_withinf = np.where(np.isnan(erfy_p1),  np.inf, erfy_p1)
            erfy_p2_withinf = np.where(np.isnan(erfy_p2), -np.inf, erfy_p2)
            erfz_p1_withinf = np.where(np.isnan(erfz_p1),  np.inf, erfz_p1)
            erfz_p2_withinf = np.where(np.isnan(erfz_p2), -np.inf, erfz_p2)

            return self.s * vertorized_erfc((x - self.vt) / self.xden)\
                * (vertorized_erf(erfy_p1_withinf) - vertorized_erf(erfy_p2_withinf))\
                * (vertorized_erf(erfz_p1_withinf) - vertorized_erf(erfz_p2_withinf))

        elif self.name == "DomenicoRobbins2D":
            yden = 2 * np.sqrt(self.dy * x)
            erfy_p1 = (y + self.yover2) / yden
            erfy_p2 = (y - self.yover2) / yden

            erfy_p1_withinf = np.where(np.isnan(erfy_p1),  np.inf, erfy_p1)
            erfy_p2_withinf = np.where(np.isnan(erfy_p2), -np.inf, erfy_p2)

            return self.s * 2 * vertorized_erfc((x - self.vt) / self.xden)\
                * (vertorized_erf(erfy_p1_withinf) - vertorized_erf(erfy_p2_withinf))

        elif self.name == "DomenicoRobbinsSS":
            yden = 2 * np.sqrt(self.dy * x)
            zden = 2 * np.sqrt(self.dz * x)
            erfy_p1 = (y + self.yover2) / yden
            erfy_p2 = (y - self.yover2) / yden
            erfz_p1 = (z + self.zover2) / zden
            erfz_p2 = (z - self.zover2) / zden

            erfy_p1_withinf = np.where(np.isnan(erfy_p1),  np.inf, erfy_p1)
            erfy_p2_withinf = np.where(np.isnan(erfy_p2), -np.inf, erfy_p2)
            erfz_p1_withinf = np.where(np.isnan(erfz_p1),  np.inf, erfz_p1)
            erfz_p2_withinf = np.where(np.isnan(erfz_p2), -np.inf, erfz_p2)

            return self.s * 2 * (vertorized_erf(erfy_p1_withinf) - vertorized_erf(erfy_p2_withinf))\
                * (vertorized_erf(erfz_p1_withinf) - vertorized_erf(erfz_p2_withinf))

        elif self.name == "DomenicoRobbinsSS2D":
            yden = 2 * np.sqrt(self.dy * x)
            erfy_p1 = (y + self.yover2) / yden
            erfy_p2 = (y - self.yover2) / yden

            erfy_p1_withinf = np.where(np.isnan(erfy_p1),  np.inf, erfy_p1)
            erfy_p2_withinf = np.where(np.isnan(erfy_p2), -np.inf, erfy_p2)

            return self.s * 4 * (vertorized_erf(erfy_p1_withinf) - vertorized_erf(erfy_p2_withinf))

        elif self.name == "DomenicoRobbinsSSDecay2D":
            xover2 = x / (2 * self.dx)
            yden = 2 * np.sqrt(self.dy * x)
            erfy_p1 = (y + self.yover2) / yden
            erfy_p2 = (y - self.yover2) / yden

            erfy_p1_withinf = np.where(np.isnan(erfy_p1),  np.inf, erfy_p1)
            erfy_p2_withinf = np.where(np.isnan(erfy_p2), -np.inf, erfy_p2)

            return self.s * 4 * (vertorized_erf(erfy_p1_withinf) - vertorized_erf(erfy_p2_withinf))\
                * np.exp(xover2 - xover2 * self.decay_sqrt)

        elif self.name == "DomenicoRobbins2DModified":
            yden = 2 * np.sqrt(self.dy * x)
            erfy_p1 = (y + self.yover2) / yden
            erfy_p2 = (y - self.yover2) / yden

            correction_exp = np.exp(x / self.dx)
            correction_erfc = vertorized_erfc((x + self.vt) / self.xden)
            condition = (correction_erfc <= 0) | np.isinf(correction_exp)
            correction = np.where(condition, 0, correction_exp * correction_erfc)

            erfy_p1_withinf = np.where(np.isnan(erfy_p1),  np.inf, erfy_p1)
            erfy_p2_withinf = np.where(np.isnan(erfy_p2), -np.inf, erfy_p2)

            return self.s * 2 * (vertorized_erfc(x - self.vt + correction) / self.xden)\
                * (vertorized_erf(erfy_p1_withinf) - vertorized_erf(erfy_p2_withinf))


if __name__ == "__main__":
    pass
