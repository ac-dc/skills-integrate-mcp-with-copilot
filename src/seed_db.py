from database import ActivityRepository


def main() -> None:
    repository = ActivityRepository()
    repository.initialize(seed=True)
    print(f"Database initialized and seeded at {repository.db_path}")


if __name__ == "__main__":
    main()
