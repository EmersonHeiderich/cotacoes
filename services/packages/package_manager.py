# services/packages/package_manager.py
class Package:
    def __init__(self, nome, comprimento, altura, largura, peso, quantidade=1):
        self.nome = nome
        self.comprimento = comprimento  # cm
        self.altura = altura  # cm
        self.largura = largura  # cm
        self.peso = peso  # kg
        self.quantidade = quantidade  # Quantidade de embalagens

    def __repr__(self):
        volume = self.get_volume()
        return (f"Package(nome={self.nome}, comprimento={self.comprimento}, "
                f"altura={self.altura}, largura={self.largura}, peso={self.peso}, "
                f"volume={volume:.4f} m³, quantidade={self.quantidade})")

    def get_volume(self):
        """Calcula o volume em metros cúbicos (m³) com dimensões em centímetros."""
        return (self.comprimento / 100) * (self.altura / 100) * (self.largura / 100)

    def to_dict(self):
        """Retorna o dicionário com os dados da embalagem."""
        volume_unitario = round(self.get_volume(), 5)
        return {
            'AmountPackages': self.quantidade,
            'Weight': self.peso,
            'Length': self.comprimento,
            'Height': self.altura,
            'Width': self.largura,
            'volume': volume_unitario,
            'nome': self.nome,
            'quantidade': self.quantidade,
            'peso': self.peso,
            'comprimento': self.comprimento,
            'altura': self.altura,
            'largura': self.largura,
            'volume_unitario': volume_unitario  # Adicionado
        }

class PackageManager:
    def __init__(self):
        self.pre_defined_packages = {
            1: {'nome': 'PP', 'comprimento': 43, 'altura': 35, 'largura': 18, 'peso': 3},
            2: {'nome': 'P', 'comprimento': 43, 'altura': 35, 'largura': 21, 'peso': 6},
            3: {'nome': 'M', 'comprimento': 70, 'altura': 43, 'largura': 21, 'peso': 10},
            4: {'nome': 'G', 'comprimento': 70, 'altura': 43, 'largura': 31, 'peso': 20},
            5: {'nome': 'Bau', 'comprimento': 43, 'altura': 35, 'largura': 31, 'peso': 10},
            6: {'nome': 'Ternos', 'comprimento': 96, 'altura': 63, 'largura': 26, 'peso': 15}
        }
        self.selected_packages = []

    def select_pre_defined_package(self, package_id, peso=None, quantidade=1):
        if package_id in self.pre_defined_packages:
            package_data = self.pre_defined_packages[package_id].copy()
            if peso is not None:
                package_data['peso'] = peso  # Permite alterar o peso da embalagem
            package = Package(quantidade=quantidade, **package_data)
            self.selected_packages.append(package)
        else:
            raise ValueError("ID de embalagem inválido.")

    def add_custom_package(self, nome, comprimento, altura, largura, peso, quantidade=1):
        package = Package(nome, comprimento, altura, largura, peso, quantidade)
        self.selected_packages.append(package)

    def get_packages_for_cotation(self):
        """Retorna os dados das embalagens para a cotação com informações agregadas."""
        packages = [package.to_dict() for package in self.selected_packages]
        total_weight = sum(p['Weight'] * p['AmountPackages'] for p in packages)
        total_packages = sum(p['AmountPackages'] for p in packages)
        total_volume = sum(p['volume'] * p['AmountPackages'] for p in packages)

        return {
            'pack': packages,
            'total_weight': total_weight,
            'total_packages': total_packages,
            'total_volume': round(total_volume, 5)
        }
