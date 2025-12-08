import json
import subprocess


def get_outdated_packages():
    """Return a list of outdated pip packages with version info."""
    result = subprocess.run(
        ['pip', 'list', '--outdated', '--format=json'],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print('Error running pip list.')
        print(result.stderr)
        return []

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print('Failed to parse pip output.')
        return []


def show_outdated(packages):
    """Print a table of outdated packages."""
    if not packages:
        print('All packages are up to date.')
        return

    print('\nOutdated packages:\n')
    print(f"{'Package':<25} {'Current':<12} {'Latest':<12}")
    print('-' * 50)
    for pkg in packages:
        print(f"{pkg['name']:<25} {pkg['version']:<12} {pkg['latest_version']:<12}")
    print()


def update_packages(packages):
    """Update all outdated packages."""
    for pkg in packages:
        name = pkg['name']
        print(f"Updating {name} ({pkg['version']} → {pkg['latest_version']}) ...")
        result = subprocess.run(['pip', 'install', '-U', name])
        if result.returncode == 0:
            print(f'Successfully updated {name}')
        else:
            print(f'Failed to update {name}')
        print('-' * 50)


if __name__ == '__main__':
    packages = get_outdated_packages()
    show_outdated(packages)

    if packages:
        answer = input('Do you want to update all outdated packages? (y/N): ').strip().lower()
        if answer == 'y':
            update_packages(packages)
        else:
            print('No packages were updated.')
