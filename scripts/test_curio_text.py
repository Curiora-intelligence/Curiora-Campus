from app.services.curio import CurioService


def main() -> None:
    curio = CurioService()

    try:
        print("=" * 72)
        print("CURIO TEXT SMOKE TEST")
        print("=" * 72)

        answer = curio.respond(
            "What is CUDA?"
        )

        print()
        print("CURIO:")
        print(answer)

    finally:
        curio.release()


if __name__ == "__main__":
    main()